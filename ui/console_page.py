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

LANE_NAMES = {"active": "Planned work", "refresh": "Refreshes", "adhoc": "One-offs"}


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
                req = _one_request(b)
                who = WB.identify(req)
            except (ValueError, IndexError) as exc:
                return js(400, {"error": str(exc)[:400]})
            return js(200, WB.worksheet(who["line"], req, (b.get("company") or "").strip(), b.get("policyType") or "New"))
        if op == "download" and method == "POST":
            # an Upload & Compare row's Download: a .zip of input and output JSON for our engine, RaaS and deviated,
            # handed to the page as base64 (the page saves it as a file)
            import base64
            try:
                req = _one_request(b)
                who = WB.identify(req)
            except (ValueError, IndexError) as exc:
                return js(400, {"error": str(exc)[:400]})
            files = WB.download(who["line"], req, (b.get("company") or "").strip(), b.get("policyType") or "New")
            return js(200, {"files": list(files), "zip": base64.b64encode(WB.download_zip(files)).decode("ascii")})
        if op == "formula" and method == "POST":
            # how the premium was computed: each step as arithmetic with its factors, checked against the engine
            return js(200, WB.formulas(str(b.get("token") or ""), b.get("side") or "both"))
        if op == "why" and method == "POST":
            # G2: why a worksheet value is what it is -- its ancestry from the worksheet's rating graph
            return js(200, WB.why(str(b.get("token") or ""), b.get("side") or "technical", int(b.get("gid") or 0),
                                  int(b.get("depth") or 3)))
        if op in ("upload", "upload-send") and method == "POST":
            # Upload & Compare: the request as given (GL or CP, read from its ProductName); rated free, or one call
            # parsed here, from the text as uploaded: a browser's JSON round trip turns 1.0 into 1, so the request
            # would no longer hash to ISO's stored answer for it
            try:
                req = _one_request(b)
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
        if op == "every" and method == "POST" and line == "CP":
            import property_rating as pr
            return js(200, {**WB.every_state(b.get("config") or {}, pr.states(), line="CP"), "notApplicable": {},
                            "describes": ""})
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


def _one_request(b: dict) -> dict:
    """The request a workbench route was handed: parsed from the text as uploaded, or one item of a list."""
    req = json.loads(b["text"]) if "text" in b else b.get("request")
    if isinstance(req, list):
        req = req[int(b.get("index") or 0)]
    return req


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
    if method == "POST" and path == "/api/console/filings/packet":
        from console import filings
        code, out = filings.upload(body or {})
        return code, json.dumps(out), "json"
    if method == "GET" and path == "/api/console/filings/jobs":
        from console import filings
        return 200, json.dumps(filings.jobs()), "json"
    if path == "/api/console/filings/test":
        # the Test tab: quick checks on our engine (factors as filed, effect as expected), queued one at a time
        from console import filing_tests as FT
        if method == "POST":
            b = body or {}
            serffs = [x["serff"] for x in __import__("console.filings", fromlist=["x"]).filings()["filings"]
                      if x.get("versions")] if b.get("all") else [str(b.get("serff") or "")]
            return 200, json.dumps({"status": FT.start([x for x in serffs if x], bool(b.get("full")))}), "json"
        got = FT.result(query.get("serff", "")) if query.get("serff") else None
        return 200, json.dumps({"result": got, "status": FT.status(), "summaries": FT.summaries()}), "json"
    if method == "POST" and path == "/api/console/filings/expected":
        from console import filing_tests as FT
        b = body or {}
        try:
            FT.set_expected(str(b.get("serff") or ""), str(b.get("company") or ""), str(b.get("state") or ""),
                            b.get("value"))
        except (TypeError, ValueError):
            return 400, json.dumps({"error": "the expected effect must be a number"}), "json"
        return 200, json.dumps({"result": FT.rejudge(str(b.get("serff") or ""))}), "json"
    if path == "/api/console/filings/iso":
        # D21: the spot check sends TECHNICAL requests only; a request ISO already answered costs nothing
        from console import filing_tests as FT
        b = body or {}
        try:
            if method == "POST":
                return 200, json.dumps(FT.iso_send(str(b.get("serff") or ""), b.get("override") or None)), "json"
            return 200, json.dumps(FT.iso_plan(query.get("serff", ""))), "json"
        except KeyError as exc:
            return 404, json.dumps({"error": str(exc)}), "json"
    if method == "GET" and path == "/api/console/filings/board":
        from console import filings
        return 200, json.dumps(filings.board()), "json"
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
  <div class="mx-head"><div><div class="eyebrow">Readiness Matrix</div><h1>Which states are ready to rely on?</h1></div>
    <p>A coverage is ready when every way of pricing it has been checked against ISO, we agree on all of them, and
    nothing has gone out of date. Start from a summary, then click a coverage, a state or a step to look inside it,
    and a cell to see what it still needs.</p></div>
  <div class="mx-stats" id="mx-stats"></div>
  <div class="mx-trend"><div class="mx-trend-hd"><span>Agreement with ISO over time</span><span class="mx-key" id="mx-key"></span></div>
    <div id="mx-chart"></div></div>
  <div class="bd-views" id="mx-views" role="tablist" aria-label="View">
    <button role="tab" data-v="cov">By coverage</button><button role="tab" data-v="state">By state</button>
    <button role="tab" data-v="todo">What's left</button><button role="tab" data-v="grid">Full matrix</button></div>
  <div class="bd-alt" id="mx-alt"><div class="mx-loading">Loading the matrix… (the first build after a change takes about half a minute)</div></div>
  <div class="mx-scroll" id="mx-gridwrap" hidden><div id="mx-grid" class="mx-grid" role="grid" aria-label="Readiness by state and coverage">
    <div class="mx-loading">Loading the matrix…</div></div></div>
</div><aside class="mx-side" id="mx-side" aria-live="polite"></aside></div></section>"""

BUILT = {"matrix": MATRIX_HTML}

MATRIX_CSS = """
.mx-wrap{display:flex;gap:0;margin:0 -32px -40px;min-height:calc(100vh - 140px)}
.mx-main{flex:1;min-width:0;padding:0 32px 40px;display:flex;flex-direction:column;gap:22px}
.mx-head{display:flex;align-items:flex-end;gap:24px;flex-wrap:wrap}
.mx-head p{margin:0;padding-bottom:6px;font-size:15px;line-height:1.6;color:var(--color-neutral-700);max-width:62ch}
.mx-stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border-top:1px solid var(--color-text);
  border-bottom:1px solid var(--color-divider)}
.mx-stats div{padding:12px 18px 12px 0;border-right:1px solid var(--color-divider);margin-right:18px}
.mx-stats div:last-child{border-right:0}
.mx-stats span{display:block;font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)}
.mx-stats b{font:400 32px/1.1 var(--font-heading)}
.mx-stats small{font-size:13.5px;color:var(--color-neutral-700);margin-left:6px}
.mx-trend-hd{display:flex;justify-content:space-between;align-items:baseline;font-size:12.5px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--color-neutral-700);margin-bottom:4px}
.mx-key{display:flex;gap:14px;text-transform:none;letter-spacing:0;font-size:13.5px;color:var(--color-text)}
.mx-key i{display:inline-block;width:14px;height:2px;vertical-align:middle;margin-right:5px;border-radius:1px}
#mx-chart{position:relative;height:120px}
#mx-chart svg{display:block;width:100%;height:100%;overflow:visible}
.mx-empty{height:100%;display:flex;align-items:center;justify-content:center;border:1px dashed var(--color-neutral-400);
  border-radius:var(--radius-md);color:var(--color-neutral-700);font-size:14px}
.mx-tip{position:absolute;pointer-events:none;background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-md);
  box-shadow:0 3px 10px color-mix(in srgb,#2d1d1a 16%,transparent);padding:6px 9px;font-size:13.5px;white-space:nowrap;z-index:5}
.mx-scroll{overflow-x:auto}
.mx-grid{display:grid;gap:4px;min-width:1040px}
.mx-loading{grid-column:1/-1;padding:24px;color:var(--color-neutral-700)}
.mx-lob{font:600 18px var(--font-heading);border-bottom:1px solid var(--color-text);padding-bottom:3px}
.mx-col{font-size:13.5px;line-height:1.2;padding:0 2px 4px;align-self:end}
.mx-colr{font-size:12px;color:var(--color-neutral-700);text-align:right;padding-bottom:4px;align-self:end}
.mx-st{display:flex;align-items:center;gap:8px;min-width:0}
.mx-st b{font:600 18px var(--font-heading);width:28px;flex:none}
.mx-st span{font-size:13.5px;color:var(--color-neutral-700);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mx-sum{display:flex;align-items:center;justify-content:flex-end;font-weight:600}
.mx-cell{width:auto;overflow:hidden;height:48px;border-radius:var(--radius-sm);cursor:pointer;display:flex;flex-direction:column;align-items:flex-start;
  justify-content:center;padding:0 6px;line-height:1.2;text-align:left;font:inherit;min-width:0;position:relative}
.mx-cell:hover{filter:brightness(.95)}
.mx-cell.verified,.bd-c.verified{background:var(--teal-soft);border-color:#9fe8cf}
.mx-cell:focus-visible,.mx-cell.sel{outline:2px solid var(--color-text);outline-offset:2px}
.mx-cell .l1,.mx-cell .l2{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.mx-cell .l1{font-size:13px;font-weight:600;letter-spacing:-.01em}
.mx-cell .l2{font-size:12px}
.mx-cell .so{position:absolute;top:3px;right:5px;font-size:11.5px}
.mx-side{width:380px;flex:none;position:sticky;top:var(--hdr,66px);align-self:flex-start;max-height:calc(100vh - var(--hdr,66px));overflow-y:auto;border-left:1px solid var(--color-divider);padding:28px;background:var(--color-panel);
  display:flex;flex-direction:column;gap:18px}
.mx-back{font-size:13.5px;text-decoration:none}
.mx-list{display:flex;flex-direction:column}
.mx-lh,.mx-li{display:grid;grid-template-columns:22px 30px 28px minmax(0,1fr) 56px;gap:8px;align-items:center}
.mx-lh{padding-bottom:5px;border-bottom:1px solid var(--color-text);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)}
.mx-lh span:last-child,.mx-ln{text-align:right}
.mx-li{padding:10px 0;border:0;border-bottom:1px solid var(--color-divider);background:transparent;font:inherit;font-size:14px;
  color:var(--color-text);text-align:left;cursor:pointer}
.mx-li:hover{background:var(--color-accent-100)}
.mx-li .chip{width:20px;height:20px;font-size:11.5px}
.mx-lc{display:flex;flex-direction:column;line-height:1.25;min-width:0}
.mx-lc small,.mx-ln small{font-size:13px;color:var(--color-neutral-700)}
.mx-ln small{display:block;font-size:11.5px}
.mx-more{align-self:flex-start;border:0;background:transparent;color:var(--color-accent-700);cursor:pointer;font:inherit;font-size:14px;padding:0;text-decoration:underline}
.mx-side h2{margin:0;font:600 24px/1.15 var(--font-heading)}
.cap2{font-size:13.5px;font-weight:600;color:var(--color-neutral-700)}
.up-gl{margin:0;display:grid;gap:8px;font-size:14px}.up-gl dt{font-weight:600}.up-gl dd{margin:0;color:var(--color-neutral-700)}
.mx-side table{width:100%;border-collapse:collapse;font-size:14px}
.mx-side td{padding:9px 0;border-bottom:1px solid var(--color-divider);vertical-align:top}
.mx-side td:last-child{text-align:right;white-space:nowrap;padding-left:10px}
.mx-need{display:flex;gap:12px;align-items:center;padding:14px 16px;border:1px solid var(--color-divider);border-radius:var(--radius-lg);background:var(--color-card)}
.mx-need b{font:600 16px var(--font-heading)}
.mx-so{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.mx-so input{font:inherit;padding:8px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-md);background:var(--color-card);flex:1;min-width:120px}
.btn{border:1px solid var(--color-accent);color:var(--color-accent);background:transparent;border-radius:var(--radius-pill);
  padding:8px 18px;cursor:pointer;font:500 14px var(--font-body)}
.btn:hover{background:var(--color-accent-100)}
.btn.primary{background:var(--teal);border-color:var(--teal);color:var(--color-text);font-weight:600}
.btn.primary:hover{background:var(--teal-hover);border-color:var(--teal-hover)}
.btn:focus-visible,.tab:focus-visible,a:focus-visible,select:focus-visible,input:focus-visible,textarea:focus-visible,summary:focus-visible{outline:2px solid var(--color-accent-500);outline-offset:2px}
select,input,textarea{border-radius:var(--radius-md)}
.btn[disabled]{opacity:.5;cursor:default}
.mx-msg{font-size:13.5px;color:var(--color-neutral-700)}
.mx-lobh{font:400 21px var(--font-heading);margin-top:6px}
.mx-sg{display:grid;grid-template-columns:190px minmax(200px,1fr) minmax(240px,1.2fr) 70px;gap:8px 14px;align-items:center;font-size:14px;min-width:760px}
.mx-sg .h{font-size:13px;color:var(--color-neutral-700)}
.mx-sg .st{cursor:pointer;border:0;background:none;font:inherit;color:var(--color-text);text-align:left;border-radius:var(--radius-sm);padding:2px 6px}
.mx-sg .st:hover,.mx-sg .st.open{background:var(--color-accent-100)}
.mx-sg .st b{font:500 16px var(--font-heading);margin-right:6px}.mx-sg .st span{color:var(--color-neutral-700);font-size:13px}
.mx-segs{display:flex;gap:3px}.mx-segs i{flex:1;height:14px;border-radius:4px}
.mx-sg .pct{text-align:right;font-weight:600}
.mx-sx{grid-column:1/-1;background:var(--color-bg);border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:12px 14px;display:grid;gap:8px}
.mx-todo{display:grid;gap:12px}
.mx-tc{border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:14px 16px;display:grid;gap:6px;background:var(--color-card);cursor:pointer;text-align:left;font:inherit;color:var(--color-text)}
.mx-tc:hover,.mx-tc.sel{background:var(--color-accent-100)}
.mx-tc .hd{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.mx-tc .hd b{font:500 18px var(--font-heading)}.mx-tc .calls{margin-left:auto;font-weight:600}
.mx-pill{display:inline-flex;border-radius:var(--radius-pill);padding:2px 11px;font-size:13px;font-weight:600}
@media (max-width:1100px){.mx-wrap{flex-direction:column}.mx-side{width:auto;border-left:0;border-top:1px solid var(--color-divider)}
  .mx-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""

MATRIX_JS = r"""
const MX={data:null,sel:null,all:false,view:'cov',openC:new Set(),openS:new Set(),todo:null,from:null};
try{const v=localStorage.getItem('mx-view');if(['cov','state','todo','grid'].includes(v))MX.view=v;}catch(e){}
const SERIES={GL:{name:'General Liability',color:'#1f8f72'},CP:{name:'Commercial Property',color:'#a66b42'}};
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
  g.innerHTML=h;mxAlt();
  if(MX.sel&&by[MX.sel])mxSide(by[MX.sel]);else{MX.sel=null;mxHome();}
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

// ---- the matrix's summary views: by coverage, by state, what's left; each drills into the cell panel (mxSide)
const MXK=['mismatch','stale','internal','verified','untested','na'];
const MXN={verified:'Passed',internal:'Checked by us only',stale:'Out of date',mismatch:'Mismatch',untested:'Not tested',na:"Doesn't apply"};
const MXSTEP={mismatch:['Sort out a mismatch','Find where ours and ISO’s calculations split, decide the cause, then check again.'],
  stale:['Refresh out-of-date answers','ISO answered on an older edition. Asking again refreshes the evidence.'],
  internal:['Compare with ISO','Our engine has checked these; ISO has not. Comparing turns them into passes or mismatches.'],
  untested:['Start testing','Nothing has been priced here yet. A test plan makes the requests.']};
function mxCellsOf(l,cov){return MX.data.cells.filter(c=>c.lob===l&&c.coverage===cov);}
function mxCount(cs){const n={};cs.forEach(c=>n[c.status]=(n[c.status]||0)+1);return n;}
function mxBar(n,t){return '<div class="bd-bar">'+['verified','internal','stale','mismatch','untested','na'].filter(k=>n[k]).map(k=>'<i class="k-'+k+'" style="width:'+(100*n[k]/t)+'%" title="'+MXN[k]+': '+n[k]+'"></i>').join('')+'</div>';}
function mxExc(cs,n){const major=Object.entries(n).sort((a,b)=>b[1]-a[1])[0][0],by={};cs.forEach(c=>{if(c.status!==major)(by[c.status]=by[c.status]||[]).push(c.state);});
  const ks=MXK.filter(k=>by[k]);return ks.length?'Mostly '+MXN[major].toLowerCase()+'. '+ks.map(k=>'<b>'+MXN[k]+':</b> '+(by[k].length>6?by[k].length+' states':by[k].sort().join(', '))).join(' · '):'Same in every state';}
function mxCovView(){const r=MX.data;
  return '<div><h3>Which coverages are ready, and where not?</h3><div class="mx-msg">One line per coverage; the bar is its states, and the states that differ are named. Click a line for its states, then a state for what it needs.</div></div>'+
    '<div class="bd-key">'+MXK.map(k=>'<span><i class="k-'+k+'"></i>'+MXN[k]+'</span>').join('')+'</div>'+
    ['GL','CP'].filter(l=>r.columns[l]).map(l=>'<div class="mx-lobh">'+SERIES[l].name+'</div>'+r.columns[l].map(cov=>{const cs=mxCellsOf(l,cov),n=mxCount(cs),id=l+'|'+cov,open=MX.openC.has(id);
      return '<div class="bd-pr'+(open?' open':'')+'" data-cov="'+esc(id)+'" tabindex="0" role="button" aria-expanded="'+open+'"><div>'+esc(cov)+'</div>'+mxBar(n,cs.length)+
        '<div class="n">'+(n.verified||0)+' of '+(cs.length-(n.na||0))+' ready</div><div class="x">'+mxExc(cs,n)+'</div></div>'+
        (open?'<div class="bd-chips">'+MXK.filter(k=>n[k]).map(k=>'<div class="lbl">'+MXN[k]+' · '+n[k]+'</div>'+cs.filter(c=>c.status===k).sort((a,b)=>a.state.localeCompare(b.state)).map(c=>
          '<button class="bd-sc k-'+k+(MX.sel===mxKey(c)?' sel':'')+'" data-k="'+esc(mxKey(c))+'" data-from="c:'+esc(id)+'" title="'+esc((BOOT.names[c.state]||c.state)+': '+MXN[k])+'">'+c.state+'</button>').join('')).join('')+'</div>':'');}).join('')).join('');}
function mxStateView(){const r=MX.data,lobs=['GL','CP'].filter(l=>r.columns[l]),states=[...new Set(r.cells.map(c=>c.state))];
  const rows=states.map(s=>{const cs=r.cells.filter(c=>c.state===s),app=cs.filter(c=>c.status!=='na');return {s,cs,p:app.length?app.filter(c=>c.status==='verified').length/app.length:0};}).sort((a,b)=>a.p-b.p||a.s.localeCompare(b.s));
  const segs=(cs,l)=>'<div class="mx-segs">'+r.columns[l].map(cov=>{const c=cs.find(x=>x.lob===l&&x.coverage===cov);return '<i class="k-'+(c?c.status:'na')+'" title="'+esc(cov+': '+(c?MXN[c.status]:'not offered'))+'"></i>';}).join('')+'</div>';
  return '<div><h3>How ready is each state?</h3><div class="mx-msg">One small block per coverage, colored by its status. Least ready first. Click a state for its coverages, then a coverage for what it needs.</div></div>'+
    '<div class="mx-scroll"><div class="mx-sg"><div class="h">State</div>'+lobs.map(l=>'<div class="h">'+SERIES[l].name+' · '+r.columns[l].length+'</div>').join('')+'<div class="h" style="text-align:right">Ready</div>'+
    rows.map(x=>{const open=MX.openS.has(x.s);return '<button class="st'+(open?' open':'')+'" data-st="'+x.s+'" aria-expanded="'+open+'"><b>'+x.s+'</b><span>'+esc(BOOT.names[x.s]||'')+'</span></button>'+
      lobs.map(l=>segs(x.cs,l)).join('')+'<div class="pct">'+Math.round(100*x.p)+'%</div>'+
      (open?'<div class="mx-sx">'+lobs.map(l=>'<div><b>'+SERIES[l].name+'</b><div>'+r.columns[l].map(cov=>{const c=x.cs.find(y=>y.lob===l&&y.coverage===cov);if(!c)return '';
        return '<button class="bd-pc'+(MX.sel===mxKey(c)?' sel':'')+'" data-k="'+esc(mxKey(c))+'" data-from="s:'+x.s+'" title="'+esc(MXN[c.status])+'"><i class="k-'+c.status+'"></i>'+esc(cov)+'</button>';}).join('')+'</div></div>').join('')+'</div>':'');}).join('')+'</div></div>';}
function mxTodoView(){const L=MX.data.stillToTest||[],g={};L.forEach(x=>(g[x.status]=g[x.status]||[]).push(x));
  if(!L.length)return '<div class="mx-need"><span class="chip verified">✓</span><div><b>Nothing left</b><div class="mx-msg">Every applicable cell has Passed.</div></div></div>';
  return '<div><h3>What’s left to do, and what it costs</h3><div class="mx-msg">Every cell that is not ready yet, grouped by the next step, with the ISO calls it takes. Click a card for its cells.</div></div><div class="mx-todo">'+
    ['mismatch','stale','internal','untested'].filter(k=>g[k]).map(k=>{const xs=g[k],calls=xs.reduce((s,x)=>s+(x.calls||0),0),by={};xs.forEach(x=>{const t=SERIES[x.lob].name+' · '+x.coverage;by[t]=(by[t]||0)+1;});
      return '<button class="mx-tc'+(MX.todo===k?' sel':'')+'" data-todo="'+k+'"><span class="hd"><span class="mx-pill k-'+k+'">'+MXN[k]+'</span><b>'+MXSTEP[k][0]+'</b><span class="mx-msg">'+xs.length+' state-coverage'+(xs.length>1?'s':'')+'</span>'+
        '<span class="calls">'+calls.toLocaleString()+' ISO call'+(calls===1?'':'s')+'</span></span><span class="mx-msg">'+MXSTEP[k][1]+'</span>'+
        '<span class="mx-msg">'+Object.entries(by).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([t,n])=>esc(t)+' '+n).join(' · ')+(Object.keys(by).length>4?' · …':'')+'</span></button>';}).join('')+'</div>';}
function mxCovSide(id){const[l,cov]=id.split('|'),cs=mxCellsOf(l,cov),n=mxCount(cs),calls=cs.reduce((s,c)=>s+(c.estRemainingCalls||0),0);
  document.getElementById('mx-side').innerHTML='<a href="#matrix" class="mx-back" id="mx-back">← Still to test</a><div class="cap2">'+SERIES[l].name+'</div><h2>'+esc(cov)+'</h2>'+
    '<div class="mx-msg">Ready in '+(n.verified||0)+' of '+(cs.length-(n.na||0))+' states · about '+calls+' ISO call'+(calls===1?'':'s')+' to finish</div>'+mxBar(n,cs.length)+
    '<table>'+MXK.filter(k=>n[k]).map(k=>'<tr><td>'+MXN[k]+'</td><td>'+n[k]+'</td></tr>').join('')+'</table><div class="mx-msg">Pick a state in the list for what it needs.</div>';
  document.getElementById('mx-back').onclick=ev=>{ev.preventDefault();MX.openC.delete(id);mxAlt();mxHome();};}
function mxStateSide(st){const cs=MX.data.cells.filter(c=>c.state===st),calls=cs.reduce((s,c)=>s+(c.estRemainingCalls||0),0);
  document.getElementById('mx-side').innerHTML='<a href="#matrix" class="mx-back" id="mx-back">← Still to test</a><div class="cap2">Readiness</div><h2>'+esc(BOOT.names[st]||st)+'</h2>'+
    '<div class="mx-msg">'+cs.filter(c=>c.status==='verified').length+' of '+cs.filter(c=>c.status!=='na').length+' coverages ready · about '+calls+' ISO call'+(calls===1?'':'s')+' to finish</div>'+
    ['GL','CP'].filter(l=>MX.data.columns[l]).map(l=>{const rs=cs.filter(c=>c.lob===l);return rs.length?'<div class="cap2">'+SERIES[l].name+'</div><table>'+rs.map(c=>'<tr><td>'+esc(c.coverage)+'</td><td><span class="mx-pill k-'+c.status+'">'+MXN[c.status]+'</span></td></tr>').join('')+'</table>':'';}).join('')+
    '<button class="btn" id="mx-tobd" style="margin-top:auto">See '+st+' on the Coverage Board</button>';
  document.getElementById('mx-back').onclick=ev=>{ev.preventDefault();MX.openS.delete(st);mxAlt();mxHome();};
  document.getElementById('mx-tobd').onclick=()=>{location.hash='#board?lob=GL&state='+encodeURIComponent(st);};}
function mxTodoSide(k){const xs=(MX.data.stillToTest||[]).filter(x=>x.status===k);
  document.getElementById('mx-side').innerHTML='<a href="#matrix" class="mx-back" id="mx-back">← Still to test</a><div class="cap2">What’s left</div><h2>'+MXSTEP[k][0]+'</h2>'+
    '<div class="mx-msg">'+MXSTEP[k][1]+'</div><div class="mx-list">'+xs.map(g=>'<button class="mx-li" data-k="'+esc(g.lob+'|'+g.state+'|'+g.coverage)+'" data-from="t:'+k+'"><span class="chip '+g.status+'">'+esc(LG[g.status].glyph)+'</span>'+
      '<b>'+esc(g.state)+'</b><span>'+esc(g.lob)+'</span><span class="mx-lc"><span>'+esc(g.coverage)+'</span><small>'+esc(g.needs)+'</small></span><span class="mx-ln">'+g.calls+'</span></button>').join('')+'</div>';
  document.getElementById('mx-back').onclick=ev=>{ev.preventDefault();MX.todo=null;mxAlt();mxHome();};}
function mxBackLabel(){const f=MX.from||'';if(f.startsWith('c:'))return f.slice(2).split('|')[1];if(f.startsWith('s:'))return BOOT.names[f.slice(2)]||f.slice(2);if(f.startsWith('t:'))return MXSTEP[f.slice(2)][0];return 'Still to test';}
function mxBack(){const f=MX.from||'';MX.from=null;if(f.startsWith('c:'))mxCovSide(f.slice(2));else if(f.startsWith('s:'))mxStateSide(f.slice(2));else if(f.startsWith('t:'))mxTodoSide(f.slice(2));else mxList();}
function mxHome(){if(MX.view==='todo'&&MX.todo)mxTodoSide(MX.todo);else if(MX.view==='cov'&&MX.openC.size)mxCovSide([...MX.openC].pop());else if(MX.view==='state'&&MX.openS.size)mxStateSide([...MX.openS].pop());else mxList();}
function mxAlt(){const v=MX.view,alt=document.getElementById('mx-alt');
  document.querySelectorAll('#mx-views button').forEach(b=>b.setAttribute('aria-selected',b.dataset.v===v));
  document.getElementById('mx-gridwrap').hidden=v!=='grid';alt.hidden=v==='grid';
  if(v==='grid'||!MX.data)return;alt.innerHTML=v==='cov'?mxCovView():v==='state'?mxStateView():mxTodoView();}
function mxPick(k,from){const c=MX.data.cells.find(x=>mxKey(x)===k);if(!c)return;MX.sel=k;MX.from=from||null;
  document.querySelectorAll('.bd-sc.sel,.bd-pc.sel,.mx-cell.sel').forEach(x=>x.classList.remove('sel'));
  document.querySelectorAll('[data-k="'+CSS.escape(k)+'"]').forEach(x=>{if(!x.classList.contains('mx-li'))x.classList.add('sel');});mxSide(c);}
document.getElementById('mx-views').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b)return;
  MX.view=b.dataset.v;try{localStorage.setItem('mx-view',MX.view);}catch(e){}mxAlt();if(!MX.sel)mxHome();});
document.getElementById('mx-alt').addEventListener('click',ev=>{
  const k=ev.target.closest('[data-k]');if(k){mxPick(k.dataset.k,k.dataset.from);return;}
  const pr=ev.target.closest('.bd-pr[data-cov]');if(pr){const id=pr.dataset.cov;MX.sel=null;if(MX.openC.has(id)){MX.openC.delete(id);mxAlt();mxHome();}else{MX.openC.add(id);mxAlt();mxCovSide(id);}return;}
  const st=ev.target.closest('.mx-sg .st');if(st){const s=st.dataset.st;MX.sel=null;if(MX.openS.has(s)){MX.openS.delete(s);mxAlt();mxHome();}else{MX.openS.add(s);mxAlt();mxStateSide(s);}return;}
  const td=ev.target.closest('[data-todo]');if(td){MX.todo=td.dataset.todo;MX.sel=null;mxAlt();mxTodoSide(MX.todo);}});
document.getElementById('mx-alt').addEventListener('keydown',ev=>{if((ev.key==='Enter'||ev.key===' ')&&ev.target.matches('.bd-pr')){ev.preventDefault();ev.target.click();}});
document.getElementById('mx-side').addEventListener('click',ev=>{const b=ev.target.closest('.mx-li[data-from]');if(b){ev.stopPropagation();mxPick(b.dataset.k,b.dataset.from);}},true);
function mxSide(c){
  const s=LG[c.status],p=c.paths,labels=(MX.data.pathLabels||{})[c.lob]||{};
  let h='<a href="#matrix" class="mx-back" id="mx-back">← '+esc(mxBackLabel())+'</a><div class="cap2">'+esc(c.lob+' · '+(BOOT.names[c.state]||c.state))+'</div><h2>'+esc(c.coverage)+'</h2>';
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
    document.querySelectorAll('.mx-cell.sel,.bd-sc.sel,.bd-pc.sel').forEach(x=>x.classList.remove('sel'));mxBack();};
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
    MX.sel=b.dataset.k;MX.from=null;document.querySelectorAll('.mx-cell.sel').forEach(x=>x.classList.remove('sel'));
    const el=document.querySelector('.mx-cell[data-k="'+CSS.escape(MX.sel)+'"]');if(el){el.classList.add('sel');el.scrollIntoView({block:'center',behavior:'smooth'});}
    mxSide(c);});
  const more=document.getElementById('mx-more');if(more)more.onclick=()=>{MX.all=!MX.all;mxList();};
  const plan=document.getElementById('mx-plan');if(plan)plan.onclick=()=>{
    const lob=L[0].lob,G=L.filter(g=>g.lob===lob);   // one line per plan: the line of the most urgent gap
    location.hash='#plan?lob='+lob+'&states='+encodeURIComponent([...new Set(G.map(g=>g.state))].join(','))+'&coverages='+encodeURIComponent([...new Set(G.map(g=>g.coverage))].join('|'));};
}
function mxOpen(c){location.hash='#board?lob='+encodeURIComponent(c.lob)+'&state='+encodeURIComponent(c.state)+'&coverage='+encodeURIComponent(c.coverage);}
document.getElementById('mx-grid').addEventListener('click',ev=>{const b=ev.target.closest('.mx-cell');if(!b)return;
  MX.sel=b.dataset.k;MX.from=null;document.querySelectorAll('.mx-cell.sel').forEach(x=>x.classList.remove('sel'));b.classList.add('sel');
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
  /* Federato's palette (federato.ai): cream ground, Meridian maroon text, Beacon teal for the one action that matters,
     Grounded brown for links, Signal orange for a mismatch (docs/compare-wireframe_20261016.html) */
  --color-bg:#f7f7e3;--color-surface:#eee9cf;--color-panel:#f1edd6;--color-card:#fcfcf3;--color-text:#2d1d1a;
  --color-divider:#d9d0b0;
  --color-accent:#4e4432;--color-accent-100:#f3ecc6;--color-accent-300:#e9d491;--color-accent-400:#d0c5a2;
  --color-accent-500:#a66b42;--color-accent-700:#8a5634;--color-accent-800:#2d1d1a;
  --teal:#47fac4;--teal-hover:#06d899;--teal-soft:#d4f6e8;
  --color-neutral-300:#e3dcc0;--color-neutral-400:#c2b893;--color-neutral-500:#a79e7f;--color-neutral-600:#7a6f57;
  --color-neutral-700:#5c5240;--color-neutral-900:#2d1d1a;
  --ox:#f55a26;--ox-tint:#fde4d9;--ox-deep:#b23a10;
  /* Federato's own faces where installed; nothing is fetched (D7) */
  --font-heading:"Reckless Standard M","Reckless",Georgia,"Times New Roman",serif;
  --font-body:Case,"Case Text",Arial,"Helvetica Neue",sans-serif;
  --radius-sm:6px;--radius-md:10px;--radius-lg:16px;--radius-pill:999px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--color-bg);color:var(--color-text);font:15px/1.55 var(--font-body);
  font-variant-numeric:tabular-nums}
a{color:var(--color-accent-700)}
header{position:sticky;top:0;z-index:30;display:flex;align-items:stretch;gap:20px;padding:0 24px;min-height:66px;
  background:var(--color-bg);border-bottom:1px solid var(--color-divider);flex-wrap:wrap}
.brand{display:flex;flex-direction:column;justify-content:center;gap:1px;min-width:200px}
.brand b{font:600 21px/1.1 var(--font-heading);letter-spacing:-.01em}
.brand span{font-size:12.5px;color:var(--color-neutral-700)}
nav{display:flex;align-items:stretch;gap:4px;flex-wrap:wrap}
.tab{display:flex;align-items:center;align-self:center;padding:6px 12px;border-radius:var(--radius-pill);color:var(--color-text);
  text-decoration:none;font:500 14px var(--font-body);white-space:nowrap}
.tab:hover{background:var(--color-accent-100)}
.tab[aria-current="page"]{background:var(--color-text);color:var(--color-bg)}
.cap{margin-left:auto;display:flex;align-items:center;gap:16px;padding:8px 0}
.lanes{display:flex;flex-direction:column;gap:5px;width:440px;max-width:100%}
.lanes .hd{display:flex;justify-content:space-between;font-size:12px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--color-neutral-700)}
.lanes .bars,.lanes .lbl{display:flex;gap:3px}
.lanes .bars{height:10px}
.lanes .bars div{border:1px solid var(--color-accent-400);border-radius:var(--radius-sm);overflow:hidden;display:flex}
.lanes .bars i{display:block;height:100%}
.lanes .lbl div{font-size:11px;overflow:hidden;text-overflow:ellipsis;color:var(--color-neutral-700);white-space:nowrap;min-width:0}
.lanes .full{border-color:var(--ox)!important}
.nums{display:flex;gap:14px;align-items:baseline}
.nums div{display:flex;flex-direction:column}
.nums span{font-size:12px;color:var(--color-neutral-700);letter-spacing:.06em;text-transform:uppercase}
.nums b{font:600 22px/1 var(--font-heading)}
.nums b.left{color:var(--color-accent-700)}
.nums small{font-size:14px;line-height:1.3}
main{padding:28px 32px 40px}
.eyebrow{font-size:12.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--color-accent-700)}
h1{margin:4px 0 0;font:400 36px/1.15 var(--font-heading);text-wrap:balance}
.pending{margin-top:18px;padding:18px;border:1px dashed var(--color-neutral-400);border-radius:var(--radius-lg);
  color:var(--color-neutral-700);max-width:640px}
.legend{display:flex;align-items:center;gap:22px;flex-wrap:wrap;font-size:13.5px;margin:0 0 24px;padding:12px 18px;
  background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-pill)}
.legend>span:first-child{font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)}
.legend .k{display:flex;align-items:center;gap:7px}
.chip{width:24px;height:24px;flex:none;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;font-size:12.5px}
.chip.verified{background:var(--teal);color:var(--color-text);border:1px solid var(--teal-hover)}
.chip.internal{background:var(--color-accent-100);color:var(--color-accent-800);border:1px solid var(--color-accent-300)}
.chip.mismatch{background:var(--ox-tint);color:var(--ox-deep);border:1.5px solid var(--ox)}
.chip.stale{background:repeating-linear-gradient(135deg,var(--color-neutral-300) 0 1.5px,transparent 1.5px 6px);
  color:var(--color-neutral-900);border:1px solid var(--color-neutral-500)}
.chip.untested{background:transparent;color:var(--color-neutral-600);border:1px dashed var(--color-neutral-400)}
.chip.na{background:var(--color-surface);color:var(--color-neutral-500);border:1px solid var(--color-surface)}
@media (max-width:900px){header{padding:0 16px}main{padding:20px 16px}.cap{margin-left:0;flex-wrap:wrap}}
/*{{CSS}}*/
</style></head><body>
<header>
  <div class="brand"><b>Rating Console</b><span>Our engine, side by side with ISO's · General Liability and Property · <a href="/" title="The rating page: paste or edit one submission and rate it">Rate a submission</a></span></div>
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
  document.getElementById('cap-hd').textContent='ISO calls · '+c.cap+' a day';
  document.getElementById('cap-ov').textContent=c.overrides?c.overrides+' override'+(c.overrides>1?'s':'')+' today':'';
  document.getElementById('cap-bars').innerHTML=c.lanes.map(l=>'<div style="flex:'+l.cap+'" class="'+(l.used>=l.cap?'full':'')+
    '" title="'+esc(l.name)+': '+l.used+' of '+l.cap+'"><i style="width:'+Math.min(100,100*l.used/l.cap)+'%;background:'+FILL[l.key]+'"></i></div>').join('');
  document.getElementById('cap-lbl').innerHTML=c.lanes.map(l=>'<div style="flex:'+l.cap+'">'+esc(l.name)+' '+l.used+'/'+l.cap+'</div>').join('');
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
  <div class="mx-head"><div><div class="eyebrow">Coverage Board</div><h1>Where have we checked our work?</h1></div>
    <p>Where ISO has priced a request and we agree, the check has passed; anything else is a gap worth a look. Start
    from a summary, then click a line, a state or a tile to look inside it, and a state or coverage to see the
    requests behind it.</p>
    <div class="bd-lines" id="bd-lines" role="group" aria-label="Line"><button data-l="GL">General Liability</button><button data-l="CP">Commercial Property</button></div></div>
  <div class="mx-stats bd-stats" id="bd-stats"></div>
  <div class="bd-views" id="bd-views" role="tablist" aria-label="View">
    <button role="tab" data-v="path">By way of pricing</button><button role="tab" data-v="state">By state</button>
    <button role="tab" data-v="map">Map</button><button role="tab" data-v="grid">Full grid</button></div>
  <div class="bd-alt" id="bd-alt"><div class="mx-loading">Loading the board…</div></div>
  <div class="mx-scroll bd-scroll" id="bd-gridwrap" hidden><div id="bd-grid" class="bd-grid"><div class="mx-loading">Loading the board…</div></div></div>
  <div class="bd-ctl"><div class="mx-trend-hd"><span>Controls × states · which inputs have been rated where</span>
    <span class="mx-key"><span><b class="bd-dot r"></b>rated there</span><span><b class="bd-dot d"></b>asked, not declarable there</span><span><b class="bd-dot"></b>never run</span></span></div>
    <div class="mx-scroll"><div id="bd-ctl"></div></div></div>
</div><aside class="mx-side" id="bd-side" aria-live="polite"></aside></div></section>"""

BUILT["board"] = BOARD_HTML

BOARD_CSS = """
.bd-lines{margin-left:auto;display:flex;border:1px solid var(--color-divider);border-radius:var(--radius-pill);overflow:hidden}
.bd-lines button{border:0;border-right:1px solid var(--color-divider);background:transparent;padding:7px 16px;cursor:pointer;
  font:inherit;font-size:14.5px;color:var(--color-text)}
.bd-lines button:last-child{border-right:0}
.bd-lines button[aria-pressed="true"]{background:var(--color-accent-100);color:var(--color-accent-800);box-shadow:inset 0 -2px 0 var(--color-accent)}
.bd-stats{grid-template-columns:1fr 1fr 1.6fr 1fr 1fr 1fr}
.bd-cats{display:grid;grid-template-columns:1fr auto;gap:1px 10px;font-size:13px;margin-top:4px}
.bd-cats .def{color:var(--ox-deep)}
.bd-grid{display:grid;gap:3px;align-items:stretch}
.bd-grp{font-size:12px;letter-spacing:.03em;color:var(--color-neutral-700);border-bottom:1px solid var(--color-text);
  padding-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bd-ph{writing-mode:vertical-rl;transform:rotate(180deg);font-size:12px;line-height:1.1;height:132px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;padding:2px 0;justify-self:center;color:var(--color-text)}
.bd-ph.hl{font-weight:700;color:var(--color-accent-800)}
.bd-colhl{height:3px;border-radius:var(--radius-sm)}
.bd-colhl.hl{background:var(--color-accent)}
.bd-st{position:sticky;left:0;z-index:2;background:var(--color-bg);display:flex;align-items:center;gap:6px;border:0;padding:0;
  cursor:pointer;font:inherit;color:var(--color-text);text-align:left;min-width:0}
.bd-st b{font:600 16px var(--font-heading);width:26px;flex:none}
.bd-st span{font-size:13px;color:var(--color-neutral-700);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bd-st.sel b{color:var(--color-accent-700);text-decoration:underline}
.bd-c{width:auto;height:30px;padding:0;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;
  cursor:pointer;font:inherit;gap:1px;border-radius:var(--radius-sm)}
.bd-c i{font-style:normal;font-size:11.5px}
.bd-c small{font-size:11px}
.bd-c.na{cursor:default}
.bd-c.sel{outline:2px solid var(--color-text);outline-offset:1px}
.bd-c.descoped{background:var(--color-surface);color:var(--color-neutral-600);border:1px dotted var(--color-neutral-500)}
.bd-v{display:flex;align-items:center;gap:8px;padding:0 8px 0 2px;min-width:0}
.bd-stk{position:sticky;left:130px;z-index:2;background:var(--color-bg);border-right:1px solid var(--color-divider)}
.bd-badge{border:1px solid var(--color-neutral-400);color:var(--color-neutral-700);padding:2px 10px;border-radius:var(--radius-pill);font-size:13px;
  font-weight:600;white-space:nowrap}
.bd-badge.Go{border-color:var(--color-accent-700);color:var(--color-accent-800);background:var(--color-accent-100)}
.bd-badge.Hold{border-color:var(--color-accent-400);color:var(--color-accent-800)}
.bd-badge.Hold.mm{border-color:var(--ox);color:var(--ox-deep)}
.bd-v span:last-child{font-size:12.5px;color:var(--color-neutral-700);line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bd-counts{display:flex;gap:6px}
.bd-counts span{flex:1;display:flex;flex-direction:column;align-items:center;padding:5px 0;border-radius:var(--radius-sm);width:auto;height:auto}
.bd-counts b{font-size:15px}
.bd-counts small{font-size:11.5px}
.bd-ctl{margin-top:8px}
.bd-dot{display:inline-block;width:10px;height:10px;border-radius:50%;border:1px dashed var(--color-neutral-400);vertical-align:middle;margin-right:5px}
.bd-dot.r{background:var(--color-accent-700);border:1px solid var(--color-accent-700)}
.bd-dot.d{background:transparent;border:1.5px solid var(--color-accent-700)}
.bd-cg{display:grid;gap:2px;align-items:center;font-size:13px}
.bd-cg .h{font-size:11px;color:var(--color-neutral-700);writing-mode:vertical-rl;transform:rotate(180deg);justify-self:center;height:22px}
.bd-cg .lab{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:6px;position:sticky;left:0;background:var(--color-bg)}
.bd-cg .grp{grid-column:1/-1;font:600 14.5px var(--font-heading);padding-top:6px;border-bottom:1px solid var(--color-divider)}
.bd-cg .dot{justify-self:center}
.bd-cg .dot .bd-dot{margin-right:0}
.bd-cg .n{font-size:12px;color:var(--color-neutral-700);text-align:right}
.bd-tbl td.st{white-space:nowrap}
.bd-views{display:flex;gap:6px;flex-wrap:wrap;background:var(--color-surface);padding:5px;border-radius:var(--radius-pill);width:fit-content;max-width:100%}
.bd-views button{font:500 14px var(--font-body);border:0;background:none;color:var(--color-neutral-700);padding:8px 16px;border-radius:var(--radius-pill);cursor:pointer}
.bd-views button[aria-selected="true"]{background:var(--color-text);color:var(--color-bg)}
.bd-alt{background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-lg);padding:20px 22px;display:flex;flex-direction:column;gap:14px;min-width:0}
.bd-alt h3{margin:0;font:400 20px/1.25 var(--font-heading)}
.bd-key{display:flex;gap:16px;flex-wrap:wrap;font-size:13.5px;color:var(--color-neutral-700)}
.bd-key i{display:inline-block;width:12px;height:12px;border-radius:4px;vertical-align:-1px;margin-right:6px}
.k-verified{background:var(--teal-hover)}.k-internal{background:var(--color-accent-300)}.k-stale{background:#f6b48f}.k-mismatch{background:var(--ox)}
.k-untested{background:var(--color-neutral-300)}.k-na,.k-descoped{background:var(--color-panel);box-shadow:inset 0 0 0 1px var(--color-divider)}
.bd-bk summary{cursor:pointer;list-style:none;display:flex;align-items:baseline;gap:10px;padding:6px 0}
.bd-bk summary::-webkit-details-marker{display:none}
.bd-bk summary::before{content:"▸";color:var(--color-accent-700);font-size:13px}.bd-bk[open] summary::before{content:"▾"}
.bd-pr{display:grid;grid-template-columns:minmax(150px,1.1fr) minmax(160px,2fr) 74px minmax(150px,1.4fr);gap:14px;align-items:center;
  padding:9px 8px;border-top:1px solid var(--color-divider);font-size:14px;cursor:pointer;border-radius:var(--radius-sm)}
.bd-pr:hover,.bd-pr.open{background:var(--color-accent-100)}
.bd-pr .g{display:block;font-size:12.5px;color:var(--color-neutral-700)}
.bd-pr .n{text-align:right;font-size:13.5px}.bd-pr .x{font-size:13px;color:var(--color-neutral-700)}.bd-pr .x b{color:var(--color-text);font-weight:600}
.bd-bar{display:flex;height:12px;border-radius:var(--radius-pill);overflow:hidden;background:var(--color-neutral-300)}
.bd-bar i{display:block;height:100%}
.bd-chips{display:flex;flex-wrap:wrap;gap:5px;padding:4px 8px 14px}
.bd-chips .lbl{width:100%;font-size:12.5px;color:var(--color-neutral-700);margin-top:4px}
.bd-sc{border:0;border-radius:8px;padding:4px 0;width:44px;font:600 12.5px var(--font-body);cursor:pointer;color:var(--color-text)}
.bd-sc:hover,.bd-sc.sel,.bd-pc:hover,.bd-pc.sel{outline:2px solid var(--color-text);outline-offset:1px}
.bd-sg{display:grid;gap:6px 12px;align-items:center;font-size:14px;min-width:720px}
.bd-sg .h{font-size:13px;color:var(--color-neutral-700);align-self:end}
.bd-sg .st{cursor:pointer;border-radius:var(--radius-sm);padding:2px 6px;border:0;background:none;font:inherit;color:var(--color-text);text-align:left}
.bd-sg .st:hover,.bd-sg .st.open{background:var(--color-accent-100)}
.bd-sg .st b{font:500 16px var(--font-heading);margin-right:6px}.bd-sg .st span{color:var(--color-neutral-700);font-size:13px}
.bd-mini{height:10px;border-radius:var(--radius-pill);background:var(--color-neutral-300);overflow:hidden;position:relative}
.bd-mini i{position:absolute;inset:0 auto 0 0;background:var(--teal-hover);opacity:.6;border-radius:var(--radius-pill)}
.bd-mini.warn{box-shadow:0 0 0 1.5px #f6b48f}
.bd-sg .pct{text-align:right;font-weight:600}
.bd-sx{grid-column:1/-1;background:var(--color-bg);border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:12px 14px;display:grid;gap:10px}
.bd-sx b.g{font:500 15px var(--font-heading)}
.bd-pc{display:inline-flex;align-items:center;gap:6px;border-radius:var(--radius-pill);padding:3px 10px;font:inherit;font-size:12.5px;margin:4px 4px 0 0;cursor:pointer;border:1px solid var(--color-divider);background:var(--color-card);color:var(--color-text)}
.bd-pc i{width:9px;height:9px;border-radius:50%;display:inline-block}
.bd-map{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:6px;max-width:760px}
.bd-tile{aspect-ratio:1;border-radius:var(--radius-sm);display:flex;flex-direction:column;align-items:center;justify-content:center;font:600 13px var(--font-body);border:0;cursor:pointer;color:var(--color-text);padding:0}
.bd-tile small{font-weight:400;font-size:11px}.bd-tile.sel{outline:2px solid var(--color-text);outline-offset:2px}.bd-tile.none{cursor:default;opacity:.5}
.bd-ramp{display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--color-neutral-700)}
.bd-ramp span{display:inline-block;width:160px;height:10px;border-radius:var(--radius-pill);background:linear-gradient(90deg,var(--color-neutral-300),var(--teal-soft),var(--teal-hover))}
#bd-mapp{font:inherit;padding:8px 12px;border:1px solid var(--color-divider);background:var(--color-card);max-width:100%}
@media (max-width:760px){.bd-pr{grid-template-columns:1fr 74px}.bd-pr .bd-bar,.bd-pr .x{grid-column:1/-1}}
"""

BOARD_JS = r"""
const BD={line:'GL',data:null,ctl:{},sel:null,state:null,hl:null,cell:null,view:'path',openP:new Set(),openS:new Set(),mapPath:''};
try{const v=localStorage.getItem('bd-view');if(['path','state','map','grid'].includes(v))BD.view=v;}catch(e){}
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
  h+='<span class="bd-st" style="cursor:default;align-self:end"><span style="letter-spacing:.08em;text-transform:uppercase;font-size:12px">State</span></span>'+
    '<span class="bd-v bd-stk" style="align-self:stretch;align-items:flex-end;padding-bottom:4px"><span style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)">Readiness</span></span>';
  cols.forEach(p=>h+='<span class="bd-ph'+(hl(p)?' hl':'')+'" title="'+esc(p.label)+'">'+esc(p.label)+'</span>');
  h+='<span class="bd-st" style="cursor:default"></span><span class="bd-v bd-stk"></span>'+cols.map(p=>'<span class="bd-colhl'+(hl(p)?' hl':'')+'"></span>').join('');
  d.rows.forEach(r=>{
    h+='<button class="bd-st'+(BD.state===r.state?' sel':'')+'" data-s="'+r.state+'" title="'+esc(BOOT.names[r.state]||r.state)+'"><b>'+r.state+'</b><span>'+esc(BOOT.names[r.state]||'')+'</span></button>';
    h+='<span class="bd-v bd-stk"><span class="bd-badge '+r.verdict.replace(' ','')+(r.counts.mismatch?' mm':'')+'">'+esc(r.verdict)+'</span><span title="'+esc(r.note)+'">'+esc(r.note)+'</span></span>';
    const aw=(d.awaiting||{})[r.state]||{};
    cols.forEach(p=>{const v=r.cells[p.id]||['untested',0,0],t=bdCellTxt(v),k=r.state+'|'+p.id;
      h+='<button class="bd-c chip '+v[0]+(aw[p.id]?' aw':'')+(BD.sel===k?' sel':'')+'" data-k="'+esc(k)+'" title="'+esc(r.state+' · '+p.label+' · '+(v[0]==='descoped'?'descoped':LG[v[0]].board)+(v[1]?' · '+v[1]+' scenario'+(v[1]>1?'s':''):''))+'"><i>'+esc(t[0])+'</i>'+(t[1]?'<small>'+t[1]+'</small>':'')+'</button>';});
  });
  g.innerHTML=h;bdAlt();
  const awb=document.getElementById('bd-aw');if(awb)awb.onclick=()=>{location.hash='#queue';};
  if(BD.sel)bdCell(BD.sel,false);else if(BD.state)bdState(BD.state);else if(BD.view==='path'&&BD.openP.size)bdPathSide([...BD.openP].pop());else bdOverview();
}

// ---- the board's summary views: the same cells read by way of pricing, by state, or on a map; each drills into the
// side panel the full grid already uses (a state: bdState; a cell: bdCell with its scenarios and Find scenarios)
const BDK=['mismatch','stale','internal','verified','untested','descoped','na'];
const BDN={verified:'Passed',internal:'Checked by us only',stale:'Out of date',mismatch:'Mismatch',untested:'Not tested',descoped:'Set aside',na:"Doesn't apply"};
// a path's plain name: no coverage prefix, no decision code ("(D8: ...)"); the full label stays in the title
function bdPlain(l){return l.replace(/^[^·]*·\s*/,'').replace(/\s*\(D\d+\b[^)]*\)/,'');}
function bdPaths(){const d=BD.data;return d.columns.flatMap(g=>g.paths.map(p=>({id:p.id,g:g.coverage,l:bdPlain(p.label),label:p.label})));}
function bdSt(r,pid){return (r.cells[pid]||['untested'])[0];}
function bdCount(pid){const n={};BD.data.rows.forEach(r=>{const k=bdSt(r,pid);n[k]=(n[k]||0)+1;});return n;}
function bdBar(n,total){return '<div class="bd-bar" role="img" aria-label="'+esc(BDK.filter(k=>n[k]).map(k=>n[k]+' '+BDN[k]).join(', '))+'">'+
  ['verified','internal','stale','mismatch','untested','descoped','na'].filter(k=>n[k]).map(k=>'<i class="k-'+k+'" style="width:'+(100*n[k]/total)+'%" title="'+BDN[k]+': '+n[k]+'"></i>').join('')+'</div>';}
function bdKey(){return '<div class="bd-key">'+['verified','internal','stale','mismatch','untested','na'].map(k=>'<span><i class="k-'+k+'"></i>'+BDN[k]+'</span>').join('')+'</div>';}
function bdApp(n){return BD.data.rows.length-(n.na||0)-(n.descoped||0);}
function bdExc(pid,n){const major=Object.entries(n).sort((a,b)=>b[1]-a[1])[0][0],by={};
  BD.data.rows.forEach(r=>{const k=bdSt(r,pid);if(k!==major)(by[k]=by[k]||[]).push(r.state);});
  const ks=BDK.filter(k=>by[k]);if(!ks.length)return 'Same in every state';
  return ks.map(k=>'<b>'+BDN[k]+':</b> '+(by[k].length>6?by[k].length+' states':by[k].join(', '))).join(' · ');}
function bdChips(pid){const by={};BD.data.rows.forEach(r=>{const k=bdSt(r,pid);(by[k]=by[k]||[]).push(r.state);});
  return BDK.filter(k=>by[k]).map(k=>'<div class="lbl">'+BDN[k]+' · '+by[k].length+'</div>'+by[k].map(s=>{const key=s+'|'+pid;
    return '<button class="bd-sc k-'+k+(BD.sel===key?' sel':'')+'"'+(k==='na'?' disabled':'')+' data-k="'+esc(key)+'" title="'+esc((BOOT.names[s]||s)+': '+BDN[k])+'">'+s+'</button>';}).join('')).join('');}
function bdPathView(){const P=bdPaths(),done=[],part=[],none=[];
  P.forEach(p=>{p.n=bdCount(p.id);const a=bdApp(p.n),v=p.n.verified||0;(a&&v>=a*0.9?done:v>0||p.n.mismatch||p.n.stale||p.n.internal?part:none).push(p);});
  const row=p=>{const open=BD.openP.has(p.id);return '<div class="bd-pr'+(open?' open':'')+'" data-p="'+esc(p.id)+'" title="'+esc(p.label)+'" tabindex="0" role="button" aria-expanded="'+open+'"><div>'+esc(p.l)+'<span class="g">'+esc(p.g)+'</span></div>'+
    bdBar(p.n,BD.data.rows.length)+'<div class="n">'+(p.n.verified||0)+' of '+bdApp(p.n)+'</div><div class="x">'+bdExc(p.id,p.n)+'</div></div>'+
    (open?'<div class="bd-chips">'+bdChips(p.id)+'</div>':'');};
  const bk=(t,sub,list,open)=>list.length?'<details class="bd-bk"'+(open?' open':'')+'><summary><h3>'+t+' · '+list.length+'</h3><span class="mx-msg">'+sub+'</span></summary>'+list.map(row).join('')+'</details>':'';
  part.sort((a,b)=>((b.n.mismatch||0)+(b.n.stale||0))-((a.n.mismatch||0)+(a.n.stale||0))||(b.n.verified||0)-(a.n.verified||0));
  return '<div><h3>Which ways of pricing have we checked?</h3><div class="mx-msg">One line per way of pricing; the bar is its '+BD.data.rows.length+' states, and the states that differ are named. Click a line to see its states, then a state to see the requests behind it.</div></div>'+bdKey()+
    bk('Partly checked','Started, with states still to do. Usually the next calls to spend.',part,true)+
    bk('Passed nearly everywhere','90% or more of the states where it applies.',done,true)+
    bk('Not started anywhere','No state has a passed check yet.',none,false);}
function bdGroups(r){return BD.data.columns.map(g=>{let v=0,a=0,w=0;g.paths.forEach(p=>{const k=bdSt(r,p.id);if(k==='na'||k==='descoped')return;a++;if(k==='verified')v++;if(k==='stale'||k==='mismatch')w++;});return {g:g.coverage,v,a,w};});}
function bdStateView(){const G=BD.data.columns.map(g=>g.coverage);
  const rows=BD.data.rows.map(r=>{const gs=bdGroups(r),v=gs.reduce((s,x)=>s+x.v,0),a=gs.reduce((s,x)=>s+x.a,0);return {r,gs,p:a?v/a:0};}).sort((x,y)=>x.p-y.p||x.r.state.localeCompare(y.r.state));
  return '<div><h3>How ready is each state?</h3><div class="mx-msg">One bar per coverage: how much of it ISO has confirmed. Least ready first; an orange ring means something there is out of date or mismatched. Click a state to see every way of pricing in it.</div></div>'+
    '<div class="mx-scroll"><div class="bd-sg" style="grid-template-columns:190px repeat('+G.length+',minmax(80px,1fr)) 64px"><div class="h">State</div>'+G.map(g=>'<div class="h">'+esc(g)+'</div>').join('')+'<div class="h" style="text-align:right">Overall</div>'+
    rows.map(x=>{const s=x.r.state,open=BD.openS.has(s);return '<button class="st'+(open?' open':'')+'" data-s="'+s+'" aria-expanded="'+open+'"><b>'+s+'</b><span>'+esc(BOOT.names[s]||'')+'</span></button>'+
      x.gs.map(g=>g.a?'<div class="bd-mini'+(g.w?' warn':'')+'" title="'+esc(g.g+': '+g.v+' of '+g.a+' passed'+(g.w?', '+g.w+' out of date or mismatched':''))+'"><i style="width:'+(100*g.v/g.a)+'%"></i></div>':'<div class="mx-msg">n/a</div>').join('')+
      '<div class="pct">'+Math.round(100*x.p)+'%</div>'+(open?'<div class="bd-sx">'+bdStateChips(x.r)+'</div>':'');}).join('')+'</div></div>';}
function bdStateChips(r){return BD.data.columns.map(g=>'<div><b class="g">'+esc(g.coverage)+'</b><div>'+g.paths.map(p=>{const k=bdSt(r,p.id),key=r.state+'|'+p.id;
  return '<button class="bd-pc'+(BD.sel===key?' sel':'')+'" data-k="'+esc(key)+'"'+(k==='na'?' disabled':'')+' title="'+esc(p.label+': '+BDN[k])+'"><i class="k-'+k+'"></i>'+esc(bdPlain(p.label))+'</button>';}).join('')+'</div></div>').join('');}
const BD_TILES=[['AK',0,0],['ME',0,11],['VT',1,10],['NH',1,11],['WA',2,1],['ID',2,2],['MT',2,3],['ND',2,4],['MN',2,5],['IL',2,6],['WI',2,7],['MI',2,8],['NY',2,9],['RI',2,10],['MA',2,11],
 ['OR',3,1],['NV',3,2],['WY',3,3],['SD',3,4],['IA',3,5],['IN',3,6],['OH',3,7],['PA',3,8],['NJ',3,9],['CT',3,10],['CA',4,1],['UT',4,2],['CO',4,3],['NE',4,4],['MO',4,5],['KY',4,6],['WV',4,7],['VA',4,8],['MD',4,9],['DE',4,10],
 ['AZ',5,2],['NM',5,3],['KS',5,4],['AR',5,5],['TN',5,6],['NC',5,7],['SC',5,8],['DC',5,9],['OK',6,4],['LA',6,5],['MS',6,6],['AL',6,7],['GA',6,8],['HI',7,0],['TX',7,4],['FL',7,9],['PR',7,11]];
function bdShade(p){if(p===null)return 'var(--color-panel)';
  return p<.5?'color-mix(in srgb,var(--teal-soft) '+Math.round(p*200)+'%,var(--color-neutral-300))':'color-mix(in srgb,var(--teal-hover) '+Math.round((p-.5)*200)+'%,var(--teal-soft))';}
function bdMapView(){const R=Object.fromEntries(BD.data.rows.map(r=>[r.state,r])),pid=BD.mapPath;
  const pct=r=>{if(!r)return null;if(pid){const k=bdSt(r,pid);return k==='na'||k==='descoped'?null:k==='verified'?1:k==='internal'?.35:0;}
    const gs=bdGroups(r),a=gs.reduce((s,x)=>s+x.a,0);return a?gs.reduce((s,x)=>s+x.v,0)/a:null;};
  return '<div><h3>Where in the country are the gaps?</h3><div class="mx-msg">Each tile is a state, shaded by how much ISO has confirmed. Pick one way of pricing to see only it; click a state for its detail.</div></div>'+
    '<div class="td-tools"><select id="bd-mapp" aria-label="Way of pricing"><option value="">Every way of pricing</option>'+bdPaths().map(p=>'<option value="'+esc(p.id)+'"'+(p.id===pid?' selected':'')+'>'+esc(p.g+' · '+p.l)+'</option>').join('')+'</select>'+
    '<span class="bd-ramp">0%<span></span>100%</span></div><div class="bd-map">'+BD_TILES.map(([s,y,x])=>{const r=R[s],p=pct(r),t=p===null?'n/a':Math.round(100*p)+'%';
      return '<button class="bd-tile'+(r?'':' none')+(BD.state===s?' sel':'')+'" data-s="'+s+'"'+(r?'':' disabled')+' style="grid-row:'+(y+1)+';grid-column:'+(x+1)+';background:'+bdShade(p)+'" title="'+esc((BOOT.names[s]||s)+': '+(r?t:'not on this board'))+'">'+s+'<small>'+(r?t:'')+'</small></button>';}).join('')+'</div>';}
function bdPathSide(pid){const p=bdPaths().find(x=>x.id===pid);if(!p)return bdOverview();const n=bdCount(pid);
  document.getElementById('bd-side').innerHTML='<a href="#" class="mx-back" id="bd-back">← Overview</a><div class="cap2">Way of pricing · '+esc(p.g)+'</div><h2>'+esc(p.l)+'</h2>'+
    '<div class="mx-msg">Passed in '+(n.verified||0)+' of '+bdApp(n)+' states where it applies.</div>'+bdBar(n,BD.data.rows.length)+
    '<table>'+BDK.filter(k=>n[k]).map(k=>'<tr><td>'+BDN[k]+'</td><td>'+n[k]+'</td></tr>').join('')+'</table><div class="mx-msg">Pick a state in the list for the requests behind it, and to find or send new ones.</div>';
  document.getElementById('bd-back').onclick=ev=>{ev.preventDefault();BD.openP.delete(pid);BD.sel=null;BD.state=null;bdDraw();};}
function bdAlt(){
  const v=BD.view,alt=document.getElementById('bd-alt');
  document.querySelectorAll('#bd-views button').forEach(b=>b.setAttribute('aria-selected',b.dataset.v===v));
  document.getElementById('bd-gridwrap').hidden=v!=='grid';alt.hidden=v==='grid';
  if(v==='grid'||!BD.data)return;
  alt.innerHTML=v==='path'?bdPathView():v==='state'?bdStateView():bdMapView();
  const m=document.getElementById('bd-mapp');if(m)m.onchange=()=>{BD.mapPath=m.value;bdAlt();};}
document.getElementById('bd-views').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b)return;
  BD.view=b.dataset.v;try{localStorage.setItem('bd-view',BD.view);}catch(e){}bdAlt();});
document.getElementById('bd-alt').addEventListener('click',ev=>{
  const c=ev.target.closest('[data-k]');if(c){BD.sel=c.dataset.k;BD.state=BD.sel.split('|')[0];
    document.querySelectorAll('.bd-sc.sel,.bd-pc.sel').forEach(x=>x.classList.remove('sel'));c.classList.add('sel');bdCell(BD.sel);return;}
  const pr=ev.target.closest('.bd-pr');if(pr){const id=pr.dataset.p;if(BD.openP.has(id)){BD.openP.delete(id);bdAlt();bdOverview();}else{BD.openP.add(id);bdAlt();bdPathSide(id);}return;}
  const st=ev.target.closest('.bd-sg .st');if(st){const s=st.dataset.s;BD.sel=null;
    if(BD.openS.has(s)){BD.openS.delete(s);BD.state=null;bdAlt();bdOverview();}else{BD.openS.add(s);BD.state=s;bdAlt();bdState(s);}return;}
  const t=ev.target.closest('.bd-tile');if(t&&!t.disabled){BD.state=t.dataset.s;BD.sel=null;bdAlt();bdState(BD.state);}});
document.getElementById('bd-alt').addEventListener('keydown',ev=>{if((ev.key==='Enter'||ev.key===' ')&&ev.target.matches('.bd-pr')){ev.preventDefault();ev.target.click();}});
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
  let h='<a href="#" class="mx-back" id="bd-back">← '+esc(BD.view==='path'&&BD.openP.has(c.key.split('|')[1])?c.label:(BOOT.names[c.state]||c.state))+'</a><div class="cap2">Selected cell · '+esc(c.line+' · '+c.state)+'</div>'+
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
  document.getElementById('bd-back').onclick=ev=>{ev.preventDefault();BD.sel=null;const pid=c.key.split('|')[1];
    if(BD.view==='path'&&BD.openP.has(pid)){BD.state=null;bdAlt();bdPathSide(pid);}else{BD.state=c.state;bdDraw();}};
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
    BD.state=p.get('state')||null;BD.sel=null;if(BD.state&&BD.view!=='grid'){BD.view='state';BD.openS.add(BD.state);}}
  bdLoad().then(()=>{if(BD.state){const b=document.querySelector(BD.view==='grid'?'.bd-st[data-s="'+BD.state+'"]':'.bd-sg .st[data-s="'+BD.state+'"]');if(b)b.scrollIntoView({block:'center'});}});
}
document.getElementById('bd-lines').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b||b.dataset.l===BD.line)return;
  BD.line=b.dataset.l;BD.sel=null;BD.state=null;BD.hl=null;BD.openP.clear();BD.openS.clear();BD.mapPath='';bdLoad();});
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
  <div class="mx-head"><div><div class="eyebrow">Trace Diff</div><h1>Where did we and ISO part ways?</h1></div>
    <p>Pick a request ISO has priced. We price it again on today's engine and line the two up step by step, so you can
    see the first number we got differently and everything that followed from it. This never uses a call.</p></div>
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
.td-pick input#td-state{width:64px;font:inherit;padding:8px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-md);background:var(--color-card);text-transform:uppercase}
.td-pick select{font:inherit;padding:8px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-md);background:var(--color-card);max-width:420px}
.td-chk{font-size:14px;display:flex;gap:5px;align-items:center}
.td-head{display:flex;gap:18px;align-items:baseline;flex-wrap:wrap}
.td-head h2{margin:0;font:600 22px var(--font-heading)}
.td-root{border:1.5px solid var(--ox);background:var(--ox-tint);border-radius:var(--radius-md);padding:10px 12px;margin:6px 0}
.td-root.ok{border-color:var(--color-accent-700);background:var(--color-accent-100)}
.td-root b{font:600 15px var(--font-heading)}
.td-root code,.td-row code{font-size:12.5px;word-break:break-all}
.td-tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.td-recs{display:flex;flex-direction:column;gap:4px}
.td-rec{border:1px solid var(--color-divider);border-radius:var(--radius-md);background:var(--color-bg)}
.td-rec>button{width:100%;display:flex;gap:10px;align-items:center;padding:6px 10px;border:0;background:transparent;cursor:pointer;font:inherit;
  text-align:left;color:var(--color-text)}
.td-rec>button span:first-child{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13.5px}
.td-rec.bad{border-color:var(--ox)}
.td-rows{width:100%;border-collapse:collapse;font-size:13.5px;table-layout:fixed}
.td-rows td:nth-child(1){width:38%}.td-rows td:nth-child(2),.td-rows td:nth-child(3){width:20%}
.td-rows td{overflow-wrap:anywhere}
#td-body{min-width:0;overflow-x:hidden}
.td-rows td{padding:8px 10px;border-top:1px solid var(--color-divider);vertical-align:top}
.td-rows td.v{text-align:right;font-variant-numeric:tabular-nums}
.td-rows tr.first td{background:var(--ox-tint)}
.td-rows tr.flows td{background:color-mix(in srgb,var(--ox-tint) 50%,transparent)}
.td-tag{font-size:12px;padding:1px 6px;border-radius:var(--radius-sm);border:1px solid var(--color-neutral-400);white-space:nowrap}
.td-tag.first{border-color:var(--ox);color:var(--ox-deep);font-weight:600}
.td-tag.flows{color:var(--ox-deep)}
.td-src{font-size:12px;color:var(--color-neutral-700)}
.td-cls select,.td-cls input,.td-cls textarea{font:inherit;padding:8px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-md);background:var(--color-card);width:100%}
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
        '<td><span class="chip '+st+'" style="width:18px;height:15px;font-size:11px">'+(r.match===true?'✓':r.match===false?'×':'·')+'</span> '+
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
  <div class="mx-head"><div><div class="eyebrow">Scenario Workbench</div><h1>Build a risk and see what it costs</h1></div>
    <p>Change any field and our price updates straight away, free. ISO's price sits beside it when ISO has already
    answered this exact risk; otherwise one click asks, never without your go.</p>
    <div class="bd-lines" id="wb-lines" role="group" aria-label="Line"><button data-l="GL">General Liability</button><button data-l="CP">Commercial Property</button></div></div>
  <div class="wb-top"><label>State <select id="wb-state"></select></label>
    <details class="wb-eng"><summary>Engine settings</summary><span class="wb-engin"><label id="wb-model">Mode <select id="wb-mode"></select></label><label id="wb-roundl">Rounding <select id="wb-round"></select></label></span></details></div>
  <div class="pl-shell">
    <nav class="wb-nav" id="wb-nav" aria-label="Screens"></nav>
    <div class="wb-col">
      <section class="wb-panel"><div><h2 id="wb-scrh"></h2><span class="mx-msg">Fields left on Standard keep the base risk.</span></div>
        <div class="pl-form" id="wb-inputs"></div>
        <details class="wb-raw" id="wb-rawd"><summary>Edit the request directly (specialists)</summary>
          <div class="mx-msg">The request as sent to the engine. Edits here replace the form until you reset them.</div>
          <textarea id="wb-req" spellcheck="false"></textarea><div class="td-tools"><button class="btn" id="wb-rawgo">Price this request</button><button class="btn" id="wb-rawreset">Back to the form</button></div></details></section>
      <section class="wb-panel"><div><h2>Across every state</h2><p class="mx-msg">The same risk priced in each state on our engine, free.</p></div>
        <div class="td-tools"><button class="btn primary" id="wb-every">Price it in every state · free</button><span class="mx-msg" id="wb-everymsg"></span></div>
        <div class="mx-stats wb-stats" id="wb-stats" hidden></div>
        <div class="bd-views" id="wb-tabs" role="tablist" aria-label="View"><button role="tab" data-t="map">Map</button><button role="tab" data-t="table">Table</button><button role="tab" data-t="curve">How one field moves the price</button></div>
        <div id="wb-across"></div>
        <div id="wb-curvebox" hidden><div class="td-tools"><select id="wb-curve"></select><span class="mx-msg" id="wb-curvemsg"></span></div>
          <div class="mx-key" style="margin:6px 0"><span><i style="background:#a66b42"></i>ours</span><span><b class="bd-dot r" style="background:#1f8f72;border-color:#1f8f72"></b>ISO</span></div>
          <div id="wb-chart" style="position:relative;height:200px"></div></div>
      </section>
    </div>
  </div>
</div><aside class="mx-side" id="wb-side" aria-live="polite"><div class="mx-msg">Pricing the base risk…</div></aside></div></section>"""

BUILT["workbench"] = WB_HTML

WB_CSS = """
.wb-top{display:flex;gap:16px;flex-wrap:wrap;align-items:center;font-size:14px}
.wb-top select,.wb-in select,.wb-in input,#wb-req,.wb-conf input{font:inherit;padding:8px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-md);background:var(--color-card);max-width:100%}
.wb-eng summary{cursor:pointer;color:var(--color-accent-700)}.wb-engin{display:inline-flex;gap:12px;margin-left:10px}
.wb-nav{position:sticky;top:calc(var(--hdr,66px) + 12px);display:flex;flex-direction:column;gap:4px}
@media (max-width:1300px){.wb-nav{flex-direction:row;flex-wrap:wrap;position:static}}
.wb-nav button{display:flex;justify-content:space-between;gap:8px;align-items:center;text-align:left;border:0;background:none;padding:9px 12px;border-radius:var(--radius-md);font:500 14.5px var(--font-body);color:var(--color-neutral-700);cursor:pointer}
.wb-nav button[aria-current="true"]{background:var(--color-card);color:var(--color-text);box-shadow:0 1px 3px color-mix(in srgb,#2d1d1a 8%,transparent)}
.wb-nav .c{font-size:11.5px;background:var(--color-accent-300);color:var(--color-text);border-radius:var(--radius-pill);padding:0 7px;white-space:nowrap}
.wb-col{display:flex;flex-direction:column;gap:22px;min-width:0}
.wb-panel{background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-lg);padding:22px 24px;display:flex;flex-direction:column;gap:16px;min-width:0}
.wb-panel h2{margin:0;font:400 23px/1.2 var(--font-heading)}
.pl-f.chg{border-color:var(--color-accent-300);background:var(--color-accent-100)}
.pl-f .hd a{margin-left:auto;font-size:12.5px;cursor:pointer}
.wb-raw summary{cursor:pointer;color:var(--color-accent-700);font-size:14px}
.wb-raw[open]{display:flex;flex-direction:column;gap:8px}
#wb-req{width:100%;min-height:220px;font-family:ui-monospace,Menlo,monospace;font-size:13px}
.wb-conf{border:1.5px solid var(--color-accent);background:var(--color-accent-100);border-radius:var(--radius-md);padding:12px;display:flex;flex-direction:column;gap:8px}
.wb-conf.full{border-color:var(--ox);background:var(--ox-tint)}
.wb-cmp{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.wb-cmp div{background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:10px 12px}
.wb-cmp span{display:block;font-size:12.5px;color:var(--color-neutral-700)}.wb-cmp b{font:400 26px var(--font-heading)}
.wb-acts{display:flex;flex-direction:column;gap:8px}.wb-acts .btn{text-align:left}
.wb-stats{grid-template-columns:repeat(5,minmax(0,1fr))}
.wb-map .bd-tile small{font-size:10.5px}
.wb-tbl{width:100%;border-collapse:collapse;font-size:14px}
.wb-tbl th{text-align:left;font-weight:600;font-size:13px;color:var(--color-neutral-700);padding:6px 10px}
.wb-tbl td{padding:8px 10px;border-top:1px solid var(--color-divider)}
.wb-tbl td.v{text-align:right;font-variant-numeric:tabular-nums}
.wb-scroll{max-height:440px;overflow:auto}
.wb-res b.big{font:400 30px var(--font-heading)}
"""

WB_JS = r"""
// ---- TC-23, consolidated: the risk as submission screens (the plan builder's), one live price beside ISO's, and one
// across-every-state panel (map, table, response curve). Every price is our engine, free; only Ask ISO spends a call.
const WB={line:'GL',spec:{},opts:null,cat:null,config:{},last:null,screen:null,raw:null,every:null,tab:'map',timer:null,seq:0};
function wbJSON(url,body){return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>r.json());}
function wbState(){return document.getElementById('wb-state').value;}
function wbLoad(){
  document.querySelectorAll('#wb-lines button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.l===WB.line));
  const go=s=>{WB.spec[WB.line]=s;const sel=document.getElementById('wb-state'),cur=sel.value;
    sel.innerHTML=s.states.map(x=>'<option'+(x===cur?' selected':'')+'>'+x+'</option>').join('');if(!s.states.includes(cur))sel.value=s.states.includes('OH')?'OH':s.states[0];
    document.getElementById('wb-mode').innerHTML=(s.modes||[]).map(m=>'<option>'+m+'</option>').join('');
    document.getElementById('wb-round').innerHTML=(s.roundings||[]).map(m=>'<option>'+m+'</option>').join('');
    document.querySelector('#s-workbench .wb-eng').hidden=WB.line!=='GL';
    document.getElementById('wb-curve').innerHTML=WB.line==='GL'?'<option value="">Choose a field…</option>'+s.controls.map(c=>'<option value="'+c.id+'">'+esc(c.label)+'</option>').join(''):'<option value="">Property curves arrive with its run store</option>';
    return wbFields();};
  return WB.spec[WB.line]?go(WB.spec[WB.line]):fetch('/api/console/workbench/spec?lob='+WB.line).then(r=>r.json()).then(go);}
// the field list: GL from the Workbench's controls with the values legal for this state and risk; Property from the
// plan builder's catalog. Both carry the same ids the plan builder uses, so a risk opens there unchanged.
function wbFields(){
  if(WB.line==='GL')return wbJSON('/api/console/workbench/options',{state:wbState(),config:WB.config}).then(o=>{WB.opts=o;
    WB.cat=WB.spec.GL.controls.map(c=>{const oc=o.controls[c.id]||{};return {id:c.id,label:c.label,group:c.group,kind:oc.values?'select':'number',values:oc.values||[],exercises:c.note||''};});wbDraw();});
  return fetch('/api/console/catalog?lob=CP&state='+wbState()).then(r=>r.json()).then(j=>{WB.cat=j.dimensions;wbDraw();});}
function wbDim(id){return (WB.cat||[]).find(d=>d.id===id);}
function wbScreens(){if(WB.line==='GL'){const known=new Set(PL_SCREENS_GL.flatMap(x=>x[3])),rest=(WB.cat||[]).map(d=>d.id).filter(id=>!known.has(id));
    return PL_SCREENS_GL.map((x,i)=>i===PL_SCREENS_GL.length-1?[x[0],x[1],x[2],x[3].concat(rest)]:x);}
  const gs=[];(WB.cat||[]).forEach(d=>{let g=gs.find(x=>x[1]===d.group);if(!g){g=[d.group,d.group,'',[]];gs.push(g);}g[3].push(d.id);});return gs;}
function wbShown(id){const dep=PL_DEPENDS[id];return WB.line!=='GL'||!dep||String(WB.config[dep[0]]??'')===dep[1];}
function wbField(id){const d=wbDim(id);if(!d||!wbShown(id))return '';const v=WB.config[id]??'',chg=v!=='';let inp;
  if(d.perState||(d.kind==='select'&&d.values.length>80))inp='<input list="wb-dl-'+id+'" data-c="'+id+'" value="'+esc(String(v))+'" placeholder="Standard · type to search '+d.values.length+'" aria-label="'+esc(d.label)+'"><datalist id="wb-dl-'+id+'">'+d.values.map(x=>'<option value="'+esc(String(x))+'">').join('')+'</datalist>';
  else if(d.kind==='select')inp='<select data-c="'+id+'" aria-label="'+esc(d.label)+'"><option value="">Standard</option>'+d.values.map(x=>'<option'+(String(x)===String(v)?' selected':'')+'>'+esc(String(x))+'</option>').join('')+'</select>';
  else inp='<input type="number" data-c="'+id+'" value="'+esc(String(v))+'" placeholder="Standard" aria-label="'+esc(d.label)+'">';
  return '<div class="pl-f'+(chg?' chg':'')+'"><div class="hd"><span>'+esc(d.label)+'</span>'+(chg?'<a data-reset="'+id+'">Reset</a>':'')+'</div>'+inp+
    (d.exercises?'<span class="why">'+esc(d.exercises.charAt(0).toUpperCase()+d.exercises.slice(1))+'</span>':'')+'</div>';}
function wbDraw(){const scs=wbScreens();if(!WB.screen||!scs.some(x=>x[0]===WB.screen))WB.screen=scs[0][0];const sc=scs.find(x=>x[0]===WB.screen);
  document.getElementById('wb-nav').innerHTML=scs.map(x=>{const n=x[3].filter(id=>(WB.config[id]??'')!=='').length;return '<button data-scr="'+esc(x[0])+'" aria-current="'+(x[0]===sc[0])+'"><span>'+esc(x[1])+'</span>'+(n?'<span class="c">'+n+' changed</span>':'')+'</button>';}).join('');
  document.getElementById('wb-scrh').textContent=sc[1];
  document.getElementById('wb-inputs').innerHTML=WB.raw?'<div class="mx-msg">Priced from the request you edited below. "Back to the form" returns to these fields.</div>':sc[3].map(wbField).join('');}
function wbBody(extra){const b={line:WB.line,state:wbState(),mode:document.getElementById('wb-mode').value,rounding:document.getElementById('wb-round').value,...(extra||{})};
  if(WB.raw)b.request=WB.raw;else b.config=WB.config;return b;}
function wbRate(){clearTimeout(WB.timer);WB.timer=setTimeout(()=>{const seq=++WB.seq,body=wbBody();
  document.getElementById('wb-side').querySelectorAll('.wb-cmp b').forEach(x=>x.style.opacity=.4);
  wbJSON('/api/console/workbench/rate',body).then(r=>{if(seq!==WB.seq)return;WB.last={...r,body};wbSide(WB.last);
    if(!WB.raw&&document.getElementById('wb-rawd').open)document.getElementById('wb-req').value=JSON.stringify(r.request,null,1);})
    .catch(e=>{document.getElementById('wb-side').innerHTML='<div class="mx-msg">'+esc(String(e))+'</div>';});},250);}
function wbSide(r){
  const labels=(MX.data&&MX.data.pathLabels&&MX.data.pathLabels[r.line])||{},s=r.stored,rated=r.outcome==='rated',iso=s&&s.outcome==='rated'?s.iso:null;
  const same=iso!=null&&rated&&+iso===+r.premium,chg=Object.entries(WB.config).filter(([k,v])=>v!==''),num=v=>v==null||v===''?'—':Number(v).toLocaleString(undefined,{maximumFractionDigits:2});
  let h='<div class="cap2">'+esc(r.body.state+' · '+(r.line==='GL'?'General Liability':'Commercial Property'))+(r.classification?' · class '+esc(r.classification.code):'')+'</div>';
  h+=rated?'<div class="wb-cmp"><div><span>Our price</span><b>'+num(r.premium)+'</b></div><div><span>ISO’s price</span><b>'+(iso!=null?num(iso):'—')+'</b></div></div>':
    '<div class="mx-need"><span class="chip mismatch">!</span><div><b>Our engine '+(r.outcome==='stopped'?'stopped':'could not price it')+'</b><div class="mx-msg">'+esc(r.detail||'')+'</div></div></div>';
  if(r.classification)h+='<div class="mx-msg">'+esc(r.classification.description||'')+' · '+esc(r.classification.basis||'')+': '+esc(r.classification.label||'')+'</div>';
  h+=s?(s.outcome==='rated'?'<span class="mx-pill '+(same?'k-verified':'k-mismatch')+'">'+(same?'✓ Same price':'× Different by '+num(Math.abs(+r.premium-+iso)))+'</span><div class="mx-msg">ISO answered this exact risk on '+esc((s.stored_at||'').slice(0,10))+(s.freshness==='stale'?' (out of date)':'')+'. Reusing it is free.</div>':
      '<span class="mx-pill k-untested">ISO would not price it</span><div class="mx-msg">'+esc(s.message||'')+'</div>'):'<span class="mx-pill k-internal">ISO not asked yet</span>';
  h+='<div id="wb-confirm"></div><div class="wb-acts"><button class="btn'+(s?'':' primary')+'" id="wb-send">'+(s?'Ask ISO again · 1 call':'Ask ISO · 1 call')+'</button>'+
    (s&&s.outcome==='rated'?'<a class="btn" href="#trace?lob='+r.line+'&scenario='+encodeURIComponent(s.scenario)+'">Find where they split</a>':'')+
    '<button class="btn" id="wb-ws">Open the worksheet</button><button class="btn" id="wb-toplan">Plan tests from this risk</button><button class="btn" id="wb-promote">Save to the Regression Library</button></div><div class="mx-msg" id="wb-pmsg"></div>';
  h+='<div class="cap2">Changed from the base risk</div><div class="pl-chiplist">'+(WB.raw?'<span>the request edited by hand</span>':chg.length?chg.map(([k,v])=>'<span>'+esc((wbDim(k)||{}).label||k)+': '+esc(String(v))+'</span>').join(''):'<span>nothing</span>')+'</div>';
  h+='<details><summary class="mx-msg">Ways of pricing it walked · '+(r.paths||[]).length+'</summary><table>'+(r.paths||[]).map(p=>'<tr><td>'+esc(labels[p]||p)+'</td></tr>').join('')+'</table><div class="mx-msg">Request hash '+esc(r.hash||'')+'</div></details>';
  document.getElementById('wb-side').innerHTML=h;
  document.getElementById('wb-send').onclick=wbSendDialog;
  document.getElementById('wb-toplan').onclick=()=>{location.hash='#plan?lob='+r.line+'&states='+encodeURIComponent(r.body.state)+'&config='+encodeURIComponent(JSON.stringify(WB.config));};
  document.getElementById('wb-ws').onclick=()=>{const text=JSON.stringify(r.request);location.hash='#compare';
    const rows=upAdd('Workbench: '+(r.line==='GL'?'General Liability':'Property')+', '+(BOOT.names[r.body.state]||r.body.state),text);if(rows[0])UP.q.then(()=>wsOpen(rows[0]));};
  document.getElementById('wb-promote').onclick=()=>{const st=s&&s.outcome==='rated'?s:null;
    wbJSON('/api/console/promote',{scenario:st?st.scenario:(r.line+'-'+r.body.state+'-wb-'+r.hash.slice(0,10)),line:r.line,state:r.body.state,origin:'workbench',
      hash:st?st.hash:'',request:st?null:r.request,ours:r.premium}).then(j=>document.getElementById('wb-pmsg').textContent=j.error?j.error:j.already?'Already in the library.':'Saved to the Regression Library.');};}
function wbSendDialog(){const body=wbBody(),el=document.getElementById('wb-confirm');
  fetch('/api/console/cap').then(r=>r.json()).then(c=>{const ad=c.lanes.find(l=>l.key==='adhoc'),full=ad.used>=ad.cap||c.used>=c.cap,st=WB.last&&WB.last.stored;
    let h='<div class="wb-conf'+(full?' full':'')+'"><b>'+(st?'Ask ISO again?':'Ask ISO about this risk?')+'</b><div>'+(st?'ISO already answered it. Reusing that answer is free; asking again uses <b>1 call</b> and keeps the old answer in history.':'This uses <b>1 ISO call</b>, recorded.')+'</div>'+
      '<div class="mx-msg">One-off calls today: '+ad.used+' of '+ad.cap+' used · '+c.left+' of '+c.cap+' left in all'+(full?' · <b>today’s limit is reached</b>, so a call needs a reason.':'')+'</div><div class="td-tools">'+
      (full?'<input id="wb-reason" placeholder="Reason for going past today’s limit" style="flex:1">':'')+'<button class="btn primary" id="wb-spend">Yes, ask ISO · 1 call</button><button class="btn" id="wb-cancel">Not now</button></div><div class="mx-msg" id="wb-sendmsg"></div></div>';
    el.innerHTML=h;
    document.getElementById('wb-cancel').onclick=()=>{el.innerHTML='';};
    document.getElementById('wb-spend').onclick=()=>{const rs=document.getElementById('wb-reason');if(full&&rs&&!rs.value.trim()){document.getElementById('wb-sendmsg').textContent='Add a reason to go past the daily limit.';return;}
      document.getElementById('wb-sendmsg').textContent='Asking ISO…';
      wbJSON('/api/console/workbench/send',{...body,reuse:false,override:rs?rs.value.trim():''}).then(j=>{if(j.error){document.getElementById('wb-sendmsg').textContent=j.error;return;}
        el.innerHTML='';fetch('/api/console/cap').then(r=>r.json()).then(drawCap);wbRate();});};});}
function wbEvery(){const msg=document.getElementById('wb-everymsg');msg.textContent='Pricing in every state on our engine… (about a minute)';
  wbJSON('/api/console/workbench/every',{line:WB.line,config:WB.config,mode:document.getElementById('wb-mode').value,rounding:document.getElementById('wb-round').value}).then(j=>{
    if(j.error){msg.textContent=j.error;return;}WB.every={...j,config:JSON.stringify(WB.config),line:WB.line};msg.textContent='';wbAcross();}).catch(e=>{msg.textContent=String(e);});}
function wbAcross(){document.querySelectorAll('#wb-tabs button').forEach(b=>b.setAttribute('aria-selected',b.dataset.t===WB.tab));
  const el=document.getElementById('wb-across'),cb=document.getElementById('wb-curvebox'),st=document.getElementById('wb-stats');cb.hidden=WB.tab!=='curve';
  if(WB.tab==='curve'){el.innerHTML='';st.hidden=true;wbCurve();return;}
  const j=WB.every;if(!j||j.line!==WB.line){el.innerHTML='<div class="mx-empty" style="height:80px">Price it in every state to fill the map and the table.</div>';st.hidden=true;return;}
  const stale=j.config!==JSON.stringify(WB.config),na=j.notApplicable||{},rows=j.rows.concat(Object.keys(na).filter(s=>!j.rows.some(r=>r.state===s)).map(s=>({state:s,outcome:'not applicable',detail:na[s]})));
  const R=Object.fromEntries(rows.map(r=>[r.state,r])),ps=rows.filter(r=>r.outcome==='rated').map(r=>+r.premium),lo=Math.min(...ps),hi=Math.max(...ps);
  const med=ps.slice().sort((a,b)=>a-b)[Math.floor(ps.length/2)],n=v=>Number(v).toLocaleString();
  st.hidden=false;st.innerHTML='<div><span>States where it is legal</span><b>'+j.applicable+'</b><small>of '+rows.length+'</small></div><div><span>Our price</span><b>'+(ps.length?n(lo)+' – '+n(hi):'—')+'</b><small>lowest to highest</small></div>'+
    '<div><span>Middle state</span><b>'+(ps.length?n(med):'—')+'</b></div><div><span>ISO already agrees</span><b>'+(j.storedAgree||0)+'</b><small>states</small></div><div><span>Calls to check the rest</span><b>'+j.callsToSend+'</b></div>';
  const note=stale?'<div class="mx-msg"><b>The risk has changed since.</b> Price it in every state again to update.</div>':'';
  if(WB.tab==='map'){const shade=p=>{const t=(p-lo)/(hi-lo||1);return t<.5?'color-mix(in srgb,var(--color-accent-300) '+Math.round(t*200)+'%,var(--color-card))':'color-mix(in srgb,var(--color-accent-500) '+Math.round((t-.5)*200)+'%,var(--color-accent-300))';};
    el.innerHTML=note+'<span class="bd-ramp">'+(ps.length?n(lo):'')+'<span style="background:linear-gradient(90deg,var(--color-card),var(--color-accent-300),var(--color-accent-500))"></span>'+(ps.length?n(hi):'')+'</span><div class="bd-map wb-map">'+BD_TILES.map(([s,y,x])=>{const r=R[s],pos='grid-row:'+(y+1)+';grid-column:'+(x+1);
      if(!r||r.outcome!=='rated')return '<button class="bd-tile none" disabled style="'+pos+'" title="'+esc(s+': '+(r?(r.detail||r.outcome):'not offered'))+'">'+s+'</button>';
      const t=(+r.premium-lo)/(hi-lo||1);return '<button class="bd-tile'+(s===wbState()?' sel':'')+'" data-st="'+s+'" style="'+pos+';background:'+shade(+r.premium)+';color:'+(t>.75?'var(--color-card)':'var(--color-text)')+'" title="'+esc(s+': ours '+r.premium+(r.stored&&r.stored.iso?' · ISO '+r.stored.iso:''))+'">'+s+'<small>'+n(r.premium)+'</small></button>';}).join('')+'</div><div class="mx-msg">Click a state to work in it.</div>';}
  else el.innerHTML=note+'<div class="wb-scroll"><table class="wb-tbl"><tr><th>State</th><th class="v">Our price</th><th class="v">ISO’s price</th><th>Result</th></tr>'+rows.sort((a,b)=>a.state.localeCompare(b.state)).map(r=>{const iso=r.stored&&r.stored.iso;
      return '<tr><td><b>'+r.state+'</b> <span class="mx-msg">'+esc(BOOT.names[r.state]||'')+'</span></td><td class="v">'+(r.premium?n(r.premium):'—')+'</td><td class="v">'+(iso?n(iso):'—')+'</td><td>'+(r.outcome!=='rated'?'<span class="mx-msg">'+esc(r.detail||r.outcome)+'</span>':iso?(+iso===+r.premium?'✓ Same price':'× Different'):'Not asked yet')+'</td></tr>';}).join('')+'</table></div>'+
    '<div class="td-tools"><button class="btn primary" id="wb-toplan2">Plan tests from this risk</button><span class="mx-msg">Sending these is a one-risk test plan; nothing is spent here.</span></div>';
  const tp=document.getElementById('wb-toplan2');if(tp)tp.onclick=()=>{const sts=rows.filter(x=>x.outcome==='rated').map(x=>x.state);location.hash='#plan?lob='+WB.line+'&states='+encodeURIComponent(sts.join(','))+'&config='+encodeURIComponent(JSON.stringify(WB.config));};}
function wbCurve(){
  const cid=document.getElementById('wb-curve').value,el=document.getElementById('wb-chart'),msg=document.getElementById('wb-curvemsg');if(!cid){el.innerHTML='<div class="mx-empty">Choose a field to see how our price (and ISO’s, where answered) moves across its values.</div>';msg.textContent='';return;}
  fetch('/api/console/workbench/curve?control='+cid).then(r=>r.json()).then(j=>{const st=wbState(),pts=(j.series||{})[st]||[],n=Object.values(j.series||{}).filter(v=>v.length>=2).length;
    msg.textContent=pts.length>=2?st+': '+pts.length+' values run · '+n+' states have a curve':pts.length?st+': only one value run so far · '+n+' states have a curve':'no runs varied this field in '+st+' · '+n+' states have a curve';
    if(pts.length<2){el.innerHTML='<div class="mx-empty">Run two or more values of this field in '+esc(st)+' (Plan tests from this risk, with the field set to Vary) to draw its curve.</div>';return;}
    const num=v=>parseFloat(String(v).replace(/[^0-9.\-]/g,''))||0;pts.sort((a,b)=>num(a.value)-num(b.value));
    const W=el.clientWidth||700,H=200,L=56,R=16,T=10,B=34,ys=pts.flatMap(p=>[+p.ours,p.iso?+p.iso:null]).filter(v=>v!=null&&!isNaN(v)),lo=Math.min(...ys),hi=Math.max(...ys);
    const x=i=>L+(W-L-R)*(pts.length<2?0.5:i/(pts.length-1)),y=v=>T+(H-T-B)*(1-(hi===lo?0.5:(v-lo)/(hi-lo)));
    let s='<svg viewBox="0 0 '+W+' '+H+'" width="100%" height="100%" role="img" aria-label="Premium by value of '+esc(cid)+' in '+st+'">';
    [lo,hi].forEach(v=>s+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+y(v)+'" y2="'+y(v)+'" stroke="var(--color-divider)"/><text x="'+(L-6)+'" y="'+(y(v)+4)+'" text-anchor="end" font-size="11" fill="var(--color-neutral-700)">'+Math.round(v).toLocaleString()+'</text>');
    s+='<polyline fill="none" stroke="#a66b42" stroke-width="2" points="'+pts.map((p,i)=>x(i)+','+y(+p.ours)).join(' ')+'"/>';
    pts.forEach((p,i)=>{s+='<circle cx="'+x(i)+'" cy="'+y(+p.ours)+'" r="4" fill="#a66b42" stroke="var(--color-bg)" stroke-width="2"><title>'+esc(p.value+': ours '+p.ours+(p.iso?' · ISO '+p.iso:''))+'</title></circle>';
      if(p.iso)s+='<circle cx="'+x(i)+'" cy="'+y(+p.iso)+'" r="6" fill="none" stroke="#1f8f72" stroke-width="2"><title>'+esc(p.value+': ISO '+p.iso)+'</title></circle>';
      s+='<text x="'+x(i)+'" y="'+(H-12)+'" text-anchor="middle" font-size="10.5" fill="var(--color-neutral-700)">'+esc(String(p.value).slice(0,14))+'</text>';});
    el.innerHTML=s+'</svg>';});}
document.getElementById('wb-lines').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b||b.dataset.l===WB.line)return;WB.line=b.dataset.l;WB.config={};WB.raw=null;WB.screen=null;WB.every=null;wbLoad().then(()=>{wbRate();wbAcross();});});
document.getElementById('wb-state').addEventListener('change',()=>{wbFields().then(wbRate);if(WB.tab==='curve')wbCurve();else wbAcross();});
document.getElementById('s-workbench').addEventListener('click',ev=>{const t=ev.target;
  const sc=t.closest('#wb-nav [data-scr]');if(sc){WB.screen=sc.dataset.scr;wbDraw();return;}
  const rs=t.closest('[data-reset]');if(rs){delete WB.config[rs.dataset.reset];wbFields().then(wbRate);return;}
  const tb=t.closest('#wb-tabs [data-t]');if(tb){WB.tab=tb.dataset.t;wbAcross();return;}
  const st=t.closest('.wb-map [data-st]');if(st){document.getElementById('wb-state').value=st.dataset.st;document.getElementById('wb-state').dispatchEvent(new Event('change'));}});
document.getElementById('wb-inputs').addEventListener('change',ev=>{const x=ev.target.closest('[data-c]');if(!x)return;const k=x.dataset.c,d=wbDim(k);
  if(x.value!==''&&d&&d.kind==='select'&&!d.values.map(String).includes(x.value)){x.value='';x.placeholder='Not one of ISO’s values here';return;}
  if(x.value==='')delete WB.config[k];else WB.config[k]=x.value;wbFields().then(wbRate);});
document.getElementById('wb-rawd').addEventListener('toggle',()=>{if(document.getElementById('wb-rawd').open&&WB.last&&!WB.raw)document.getElementById('wb-req').value=JSON.stringify(WB.last.request,null,1);});
document.getElementById('wb-rawgo').onclick=()=>{try{WB.raw=JSON.parse(document.getElementById('wb-req').value);}catch(e){document.querySelector('#wb-rawd .mx-msg').textContent='Not valid JSON: '+e.message;return;}wbDraw();wbRate();};
document.getElementById('wb-rawreset').onclick=()=>{WB.raw=null;wbDraw();wbRate();};
document.getElementById('wb-every').onclick=wbEvery;
document.getElementById('wb-curve').onchange=wbCurve;
let wbStarted=false;function wbRoute(){if((location.hash||'').startsWith('#workbench')&&!wbStarted){wbStarted=true;wbLoad().then(()=>{wbRate();wbAcross();});}}
addEventListener('hashchange',wbRoute);wbRoute();
"""


# ---- Upload & Compare: the landing screen ---------------------------------------------------------------------------
# Requests the user already has (GL or CP, ISO's own request format, one per file or a list): the line and state read
# from ProductName, each rated on our engine (free) beside ISO's stored answer for exactly that request when there is
# one; the rest sent to ISO only after a confirmation that says what it spends (ad hoc lane, through the ledger).

UP_HTML = """<section class="screen" id="s-compare" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Compare</div><h1>Does our price match ISO's?</h1></div>
    <p>Pick a policy to price. Our engine works it out straight away, free, and ISO's answer appears beside it once you
    ask. Nothing goes to ISO until you confirm.</p></div>
  <section class="up-panel" aria-labelledby="up-h1">
    <div class="up-phd"><span class="up-n">1</span><h2 id="up-h1">Generate a request</h2>
      <span class="mx-msg">We fill in a working sample for the state you pick.</span></div>
    <div class="up-fields">
      <label for="up-lob">Line<select id="up-lob"><option value="GL">General Liability</option><option value="CP">Commercial Property</option></select></label>
      <label for="up-state">State<select id="up-state"></select></label>
      <label for="up-company">Writing company (optional)<select id="up-company"><option value="">None, ISO only</option></select></label>
      <label for="up-pt">Business<select id="up-pt"><option>New</option><option>Renewal</option></select></label>
    </div>
    <div class="td-tools"><button class="btn primary" id="up-gen-cmp">Compare with ISO</button>
      <button class="btn" id="up-gen">Just price it <span class="up-free">· free</span></button></div>
    <div class="mx-msg" id="up-comsg">With a writing company, each request is priced twice: once as ISO's rules stand (the version ISO is
      asked about) and once with the company's filed changes, which never goes to ISO. Click the company's price to see each change.</div>
    <details class="up-paste"><summary>Have your own request? Upload or paste it</summary>
      <label class="up-drop" id="up-drop"><input type="file" id="up-file" accept=".json,application/json" multiple hidden>
        <b>Drop request files here, or choose files</b><span class="mx-msg">.json, one request per file or a list of them. General Liability and Property can be mixed.</span></label>
      <textarea id="up-text" spellcheck="false" placeholder='{"header": {...}, "body": {"SchemeKeys": {"ProductName": "General Liability OH", ...}, ...}}'></textarea>
      <div class="td-tools"><button class="btn primary" id="up-add-cmp">Compare with ISO</button><button class="btn" id="up-add">Just price it <span class="up-free">· free</span></button></div></details>
  </section>
  <div id="up-confirm"></div>
  <section class="up-panel" aria-labelledby="up-h2">
    <div class="up-phd"><span class="up-n">2</span><h2 id="up-h2">How they compare</h2><span class="mx-msg" id="up-msg"></span></div>
    <div id="up-out"><div class="mx-empty">No requests yet. Generate one above, or upload your own.</div></div>
    <div class="td-tools"><button class="btn primary" id="up-send">Compare with ISO</button><button class="btn" id="up-clear">Clear the list</button></div>
  </section>
  <div id="up-ws"></div>
</div><aside class="mx-side" id="up-side" aria-live="polite"></aside></div></section>"""

BUILT["compare"] = UP_HTML

UP_CSS = """
.up-drop{display:flex;flex-direction:column;gap:4px;align-items:center;justify-content:center;text-align:center;min-height:110px;margin:0;
  border:1.5px dashed var(--color-neutral-400);border-radius:var(--radius-lg);background:var(--color-bg);cursor:pointer;padding:20px}
.up-drop.over{border-color:var(--color-accent-700);background:var(--color-accent-100)}
.up-paste summary{cursor:pointer;font-size:14.5px}
#up-text{width:100%;min-height:140px;font:13px ui-monospace,Menlo,monospace;padding:10px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-md)}
.up-tbl{width:100%;border-collapse:collapse;font-size:14px;margin-top:10px}
.up-tbl th{text-align:left;font-weight:600;font-size:12.5px;color:var(--color-neutral-700);padding:6px 10px}
.up-tbl td{padding:12px 10px;border-top:1px solid var(--color-divider);vertical-align:top}
.up-tbl .v{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.up-tbl .file{max-width:240px;overflow-wrap:anywhere}
.up-tbl .x{border:0;background:none;cursor:pointer;color:var(--color-neutral-600);font-size:15px}
.up-res{display:flex;gap:6px;align-items:flex-start}
.up-tbl .w{font-size:13px;color:var(--color-accent-700);background:var(--color-accent-100);border-radius:var(--radius-md);padding:3px 6px;max-width:420px}
.up-panel{background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-lg);padding:22px 24px;
  display:flex;flex-direction:column;gap:16px;box-shadow:0 1px 3px color-mix(in srgb,#2d1d1a 6%,transparent)}
.up-phd{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.up-phd h2{margin:0;font:400 23px/1.2 var(--font-heading)}
.up-n{font:400 23px/1 var(--font-heading);color:var(--color-accent-700)}
.up-fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}
.up-fields label{display:flex;flex-direction:column;gap:5px;font-size:13.5px;color:var(--color-neutral-700)}
.up-fields select{font:inherit;font-size:15px;color:var(--color-text);padding:9px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-md);background:#fff}
.up-free{font-weight:400;opacity:.8}
.up-paste{border-top:1px solid var(--color-divider);padding-top:14px}
.up-paste[open]{display:flex;flex-direction:column;gap:12px}
.up-paste summary{color:var(--color-accent-700)}
.up-res .chip{margin-top:-1px}
.up-cf{background:var(--color-accent-100);border:1px solid var(--color-accent-300);border-radius:var(--radius-lg);padding:18px 22px;display:flex;flex-direction:column;gap:10px}
.up-cf.full{border-color:var(--ox);background:var(--ox-tint)}
.up-cf h3{margin:0;font:400 21px/1.2 var(--font-heading)}
.up-cf ul{margin:0;padding-left:20px;display:grid;gap:4px}
.up-cf input{font:inherit;padding:8px 12px;border:1px solid var(--color-divider);background:#fff;flex:1;min-width:200px}
.up-tbl .acts{white-space:nowrap}.up-tbl .acts a{margin-right:8px;cursor:pointer}
.ws{margin-top:18px;border-top:2px solid var(--color-neutral-700);padding-top:10px}
.ws-hd{display:flex;gap:18px;flex-wrap:wrap;align-items:baseline}.ws-hd h2{margin:0;font-size:18px}
.ws-prem{display:flex;gap:22px;margin:8px 0}.ws-prem div{font-size:13.5px}.ws-prem b{display:block;font-size:20px;font-variant-numeric:tabular-nums}
.ws-tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0 4px;font-size:14px}
.ws-tools button.on{background:var(--color-accent-100);border-color:var(--color-accent-700)}
.ws-tbl{width:100%;border-collapse:collapse;font-size:13.5px}
.ws-tbl th{text-align:left;font-size:12.5px;color:var(--color-neutral-700);padding:8px 10px;position:sticky;top:0;background:var(--color-bg)}
.ws-tbl td{padding:7px 10px;border-top:1px solid var(--color-divider);vertical-align:top}
.ws-tbl .v{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.ws-tbl tr.rec td{background:var(--color-surface);font-weight:600;cursor:pointer;overflow-wrap:anywhere}
.ws-tbl td.bad{color:var(--ox-deep);font-weight:600}.ws-tbl td.chg{background:var(--color-accent-100);font-weight:600}
.fx-wrap{margin-top:8px;font-size:14px}
details.fx{border-left:2px solid var(--color-divider);margin:4px 0 4px 6px;padding:2px 0 2px 10px}
details.fx>summary{cursor:pointer;padding:2px 0}
.fx-n{font-weight:600}.fx-v{font-variant-numeric:tabular-nums;margin-left:4px}
.fx-eq{margin:3px 0 2px 14px;line-height:1.9;overflow-wrap:anywhere}
.fx-t{display:inline-block;border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:0 5px;background:var(--color-card);white-space:nowrap}
.fx-t b{font-variant-numeric:tabular-nums}
.fx-op{color:var(--color-neutral-700);font-weight:600;padding:0 3px}
.fx-aff,.fx-t.fx-aff{background:var(--color-accent-100)}
.fx-no{color:var(--color-neutral-700)}
.fx-3{display:inline-block;margin-left:10px;font-variant-numeric:tabular-nums;font-weight:600}
.fx-3 i{font-style:normal;font-weight:400;font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--color-neutral-700)}
.fx-was{color:var(--color-neutral-700);font-weight:400}
.fx-tech{color:var(--color-neutral-700)}.fx-tech i{font-style:normal;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
.fx-src{margin:2px 0 4px 14px;padding-left:16px;font-size:13px}
.fx-leaf{margin:4px 0 4px 18px}
.ws-tbl a.ws-why{cursor:pointer;color:inherit;text-decoration:underline dotted;text-underline-offset:2px}
.wy ul{list-style:none;margin:0;padding-left:14px;border-left:1px solid var(--color-divider)}.wy ul.wy-root{padding-left:0;border:0}
.wy li{margin:3px 0;font-size:13.5px;overflow-wrap:anywhere}.wy-v{font-weight:600;font-variant-numeric:tabular-nums}
.wy-k{color:var(--color-neutral-700);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.wy li.wy-aff>.wy-v,.wy li.wy-aff>.wy-name{background:var(--color-accent-100)}.wy li.wy-ctl>.wy-name{font-style:italic}
.wy-more{cursor:pointer;font-size:12.5px;margin-left:4px}.wy-src li{border:0}
.ws-tbl tr.ws-app td{border-top:1px dashed var(--color-accent-700)}.ws-tbl tr.ws-app td:first-child{font-weight:600}
.ws-tbl .src{color:var(--color-neutral-700);font-size:12.5px;overflow-wrap:anywhere;max-width:340px}
.ws-scroll{max-height:70vh;overflow:auto;border:1px solid var(--color-divider);border-radius:var(--radius-md)}
.up-co{margin-top:8px}.up-tbl a.car{cursor:pointer;font-weight:600}.up-tbl tr.sel td{background:var(--color-accent-100)}
.up-dv table{width:100%;font-size:13.5px;table-layout:fixed}.up-dv td{padding:5px 0;overflow-wrap:anywhere;vertical-align:top}
.up-dv td:first-child{width:42%;padding-right:6px}.up-dv td+td{text-align:right}.up-dv .w{color:var(--color-neutral-700);font-size:13px;margin-top:6px}
"""

UP_JS = r"""
const UP={rows:[],seq:0,busy:false,q:Promise.resolve(),spec:{}};
function money(v){if(v===null||v===undefined||v==='')return v;const n=Number(v);return isFinite(n)?n.toFixed(2):String(v);}
function signed(v){const n=Number(v);return isFinite(n)?(n>=0?'+':'')+n.toFixed(2):String(v);}
function isPrem(r){return /Premium(Sum)?$/i.test(r.field||'');}   // a premium, not PremiumIndicator or a ...PremiumAnd...Factor
function upAdd(name,text){   // the rows it added (none when the text is not JSON)
  let v;try{v=JSON.parse(text);}catch(e){UP.rows.push({id:++UP.seq,name,err:'We could not read this request (not valid JSON): '+e.message});upDraw();return [];}
  const list=Array.isArray(v)?v:[v],added=[];
  list.forEach((_,i)=>{const row={id:++UP.seq,name:list.length>1?name+' #'+(i+1):name,text,index:i,list:Array.isArray(v),busy:'rating'};UP.rows.push(row);added.push(row);upRate(row);});
  upDraw();return added;
}
function upRate(row){row.busy='rating';
  const co=UP.company||'',pt=UP.pt||'New';
  return UP.q=UP.q.then(()=>wbJSON('/api/console/workbench/upload',{text:row.text,index:row.index,company:co,policyType:pt}).then(r=>{row.busy='';if(r.error)row.err=r.error;else{row.err='';row.r=r;}upDraw();})
    .catch(e=>{row.busy='';row.err=String(e);upDraw();}));}
// the rows ISO has not answered yet
function upNeeds(){return UP.rows.filter(x=>x.r&&!x.busy&&!x.r.stored);}
// Compare with ISO is never disabled. It confirms the rows given, else the ones not asked yet, else (all answered)
// asks again for every priced row; with nothing priced it makes a request from the generator first.
function upCompare(rows){const msg=document.getElementById('up-msg');
  if(UP.busy){msg.textContent='ISO is still answering the last batch. Compare again once it finishes.';return;}
  const go=()=>{const ok=x=>x.r&&!x.busy&&x.r.outcome==='rated';
    let need=(rows||[]).filter(ok);if(!rows){need=upNeeds().filter(ok);if(!need.length)need=UP.rows.filter(ok);}
    if(need.length){upSendDialog(need);return;}
    msg.textContent=rows&&rows.length?'Our engine could not price this request, so there is nothing to ask ISO about. The reason is in the list.':'Nothing to compare yet.';};
  if(rows||UP.rows.some(x=>!x.err)){UP.q.then(go);return;}
  upGen().then(added=>{rows=added;UP.q.then(go);});}
function upVerdict(r){const s=r.stored;
  if(!s)return '<span class="up-res"><span class="chip untested">·</span><span>Not asked yet</span></span>';
  if(s.outcome!=='rated')return '<span class="up-res"><span class="chip untested">·</span><span>ISO would not price it<div class="mx-msg">'+esc((s.message||'').slice(0,160))+'</div></span></span>';
  if(r.outcome!=='rated')return '<span class="up-res"><span class="chip mismatch">×</span><span>ISO priced it; ours could not ('+esc(r.outcome)+')</span></span>';
  const d=Number(r.premium)-Number(s.iso);
  return d===0?'<span class="up-res"><span class="chip verified">✓</span><span>Same price</span></span>':
    '<span class="up-res"><span class="chip mismatch">×</span><span>Ours is '+esc(Math.abs(d).toFixed(2))+(d>0?' higher':' lower')+'</span></span>';}
function upDraw(){
  const out=document.getElementById('up-out');
  if(!UP.rows.length)out.innerHTML='<div class="mx-empty">No requests yet. Generate one above, or upload your own.</div>';
  else out.innerHTML='<table class="up-tbl"><tr><th>Request</th><th>Line · state</th><th>Effective</th><th class="v" title="Our engine, ISO&#39;s rules as filed">Our price</th><th class="v">ISO&#39;s price</th><th class="v" title="Our price after the writing company&#39;s filed changes">With company</th><th>Result</th><th></th></tr>'+
    UP.rows.map(x=>{const r=x.r,s=r&&r.stored,rm='<button class="x" data-x="'+x.id+'" title="Remove">×</button>';
      if(x.err)return '<tr><td class="file">'+esc(x.name)+'</td><td colspan="6"><span class="up-res"><span class="chip mismatch">!</span><span>'+esc(x.err)+'</span></span></td><td>'+rm+'</td></tr>';
      if(!r)return '<tr><td class="file">'+esc(x.name)+'</td><td colspan="6" class="mx-msg">Pricing on our engine…</td><td></td></tr>';
      const ours=r.outcome==='rated'?esc(money(r.premium)):esc(r.outcome);
      const iso=x.busy==='sending'?'<span class="mx-msg">asking ISO…</span>':!s?'<span class="mx-msg">not asked</span>':s.outcome==='rated'?esc(money(s.iso))+'<div class="mx-msg">'+esc((s.stored_at||s.date||'').slice(0,10))+(s.freshness==='stale'?' · out of date':'')+'</div>':'<span class="mx-msg">would not price</span>';
      return '<tr'+(UP.sel===x.id?' class="sel"':'')+'><td class="file">'+esc(x.name)+(r.outcome!=='rated'?'<div class="mx-msg">'+esc((r.detail||'').slice(0,200))+'</div>':'')+upNotes(r)+'</td><td>'+(r.line==='GL'?'General Liability':'Property')+' · '+esc(r.state)+'</td><td>'+esc(r.effective)+
        '</td><td class="v">'+ours+'</td><td class="v">'+iso+'</td><td class="v">'+upCarrier(x)+'</td><td>'+upVerdict(r)+'</td><td>'+
        '<span class="acts">'+(s&&s.outcome==='rated'?'<a href="#trace?lob='+r.line+'&scenario='+encodeURIComponent(s.scenario)+'" title="Trace Diff: the first step where the two calculations part">Find where they split</a>':'')+'<a data-ws="'+x.id+'" title="Every field, ours beside ISO\'s">Worksheet</a><a data-dl="'+x.id+'" title="Save input and output JSON for our engine, RaaS and deviated as one .zip">Download</a>'+(s&&!x.busy&&!UP.busy?'<a data-again="'+x.id+'" title="Uses one ISO call, though an answer is stored">Ask ISO again</a>':'')+'<a data-ed="'+x.id+'" title="Copy into the paste box to change it">Edit</a></span>'+rm+'</td></tr>';}).join('')+'</table>';
  const n=upNeeds().length,b=document.getElementById('up-send');
  b.textContent=n?'Compare with ISO · '+n+' not asked yet':UP.rows.some(x=>x.r)?'Ask ISO again':'Compare with ISO';
  upSide();
}
// B-07 part 4/5: our notices (not offered; R30 a coverage priced $0 or $1 silently; R31) and ISO's own messages
function upNotes(r){if(!r||r.outcome!=='rated')return '';let h='';
  (r.notices||[]).forEach(n=>{h+='<div class="w" style="margin-top:4px"><b>'+(n.startsWith('Not offered')?'Note':'Check')+':</b> '+esc(n.slice(0,240))+'</div>';});
  const m=r.messages||[];if(m.length)h+='<div class="mx-msg" title="'+esc(m.join('\n'))+'">ISO message'+(m.length>1?'s':'')+' ('+m.length+'): '+esc(m[0].slice(0,140))+(m.length>1?' …':'')+'</div>';
  return h;}
function upCarrier(x){const r=x.r,c=r&&r.carrier;
  if(!c)return '<span class="mx-msg">—</span>';
  if(c.outcome!=='rated')return '<a class="car" data-dv="'+x.id+'">refused</a>';
  const d=r.premium!=null?Number(c.premium)-Number(r.premium):null;
  return '<a class="car" data-dv="'+x.id+'" title="What the deviations did">'+esc(money(c.premium))+'</a>'+(d!==null?'<div class="mx-msg">'+signed(d)+' vs technical</div>':'');}
function upDev(x){const r=x.r,d=r.deviation||{},k=(t,v)=>'<tr><td>'+t+'</td><td style="text-align:right">'+v+'</td></tr>';
  const f=(d.filings||[]).map(f=>esc(f.id)+' v'+f.version+'<br>new '+esc(f.new_eff)+'<br>renewal '+esc(f.renewal_eff)).join('<br>')||'<i>no filing in force</i>';
  return '<div class="cap2">What the deviations did</div><div class="up-dv"><b>'+esc(x.name)+'</b><table>'+
    k('Writing company',esc(r.company)+' · '+esc(r.policyType))+k('Filing',f)+k('ISO edition',esc(d.edition||''))+
    k('Technical (pure ISO)',esc(money(d.technicalPremium)??'—'))+k('Carrier',esc(money(d.carrierPremium)??'—'))+'</table>'+
    '<div class="cap2" style="margin-top:8px">Step by step</div><table>'+(d.waterfall||[]).map(s=>k(esc(s.step),esc(signed(s.effect)))).join('')+'</table>'+
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
const WS={d:null,name:'',filter:'all',q:'',shut:new Set(),view:'calc',why:null,fx:{},fxSide:'deviated'};
function wsOpen(x){const el=document.getElementById('up-ws');WS.name=x.name;WS.shut=new Set();
  el.innerHTML='<div class="ws"><div class="mx-msg">Building the worksheet for '+esc(x.name)+'… (two ratings, no ISO call)</div></div>';el.scrollIntoView({block:'start'});
  wbJSON('/api/console/workbench/worksheet',{text:x.text,index:x.index,company:(x.r&&x.r.company)||'',policyType:(x.r&&x.r.policyType)||'New'})
    .then(d=>{WS.d=d;WS.fx={};wsDraw();}).catch(e=>{el.innerHTML='<div class="ws"><div class="mx-empty">'+esc(String(e))+'</div></div>';});}
function wsShown(){const d=WS.d,q=WS.q.toLowerCase();
  return d.rows.filter(r=>(WS.filter==='all'||(WS.filter==='diff'&&(r.techIso===false||r.changed))||(WS.filter==='dev'&&r.changed)||
    (WS.filter==='iso'&&r.techIso===false)||(WS.filter==='num'&&r.kind==='number'))&&(!q||(r.path+' '+r.rule).toLowerCase().includes(q)));}
function wsCell(v,r){return v===null||v===undefined?'<span class="mx-msg">—</span>':esc(String(r&&isPrem(r)?money(v):v));}
function wsVal(r,side){const v0=side==='technical'?r.technical:r.deviated,g=side==='technical'?r.tg:r.dg,v=isPrem(r)?money(v0):v0;
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
    '<div class="ws-prem"><div>Technical<b>'+wsCell(money(P.technical))+'</b>our engine, pure ISO</div><div>ISO<b>'+wsCell(money(P.iso))+'</b>its answer to the same request'+esc(isoNote)+'</div>'+
    (hasDev?'<div>Deviated<b>'+wsCell(money(P.deviated))+'</b>our engine with the filing, never sent to ISO</div>':'')+'</div>'+
    '<div class="ws-tools">'+btn('all','All fields · '+d.rows.length)+btn('diff','Any difference · '+cnt(r=>r.techIso===false||r.changed))+
    (hasDev?btn('dev','Deviated changes · '+cnt(r=>r.changed)):'')+btn('iso','Technical ≠ ISO · '+cnt(r=>r.techIso===false))+btn('num','Numbers only')+
    '<span style="margin-left:8px">View</span>'+['formula','calc','record'].map(v=>'<button class="btn'+(WS.view===v?' on':'')+'" data-wv="'+v+'">'+({formula:'Formula',calc:'By calculation',record:'By record'})[v]+'</button>').join('')+
    '<input id="ws-q" placeholder="Find a field, record or rule" value="'+esc(WS.q)+'" style="flex:1;min-width:180px"><button class="btn" data-wcsv="1">Download CSV</button></div>'+
    (WS.view==='formula'?fxPanel(d,hasDev):'<div class="ws-scroll"><table class="ws-tbl"><tr><th>Field</th><th class="v">Technical</th><th class="v">ISO</th>'+(hasDev?'<th class="v">Deviated</th>':'')+'<th>Written by (technical)</th></tr>'+
    Object.entries(by).map(([rec,rs])=>{const shut=WS.shut.has(rec);
      const calc=WS.view==='calc',parts=calc?[]:rec.split('/').filter(Boolean),name=calc?rec:(parts.pop()||'(policy)'),trail=parts.map(x=>x.replace(/^CommercialProperty|^GeneralLiability/,'')||x).join(' › ');
      return '<tr class="rec" data-rec="'+esc(rec)+'" title="'+esc(rec)+'"><td colspan="'+(hasDev?5:4)+'">'+(shut?'▸ ':'▾ ')+esc(name)+' <span class="mx-msg">'+rs.length+' field'+(rs.length>1?'s':'')+(trail?' · in '+esc(trail):'')+'</span></td></tr>'+
        (shut?'':rs.map(r=>'<tr'+(r.applied?' class="ws-app"':'')+'><td title="'+esc(r.path)+'">'+esc(calc?(r.label||r.field):r.field)+(r.note?'<div class="mx-msg">'+esc(r.note)+'</div>':'')+'</td><td class="v">'+wsVal(r,'technical')+'</td><td class="v'+(r.techIso===false&&d.iso==='rated'?' bad':'')+'">'+wsCell(r.iso,r)+'</td>'+
          (hasDev?'<td class="v'+(r.changed?' chg':'')+'">'+wsVal(r,'deviated')+'</td>':'')+'<td class="src">'+esc(r.rule||'')+(r.tables&&r.tables.length?' · '+esc(r.tables.join(', ')):'')+'</td></tr>').join(''));}).join('')+
    '</table></div>')+(WS.view==='formula'?'':'<div class="mx-msg">Click a technical or deviated value to see what it was computed from. By calculation: one section per coverage group of each rated item, its factors in the order our engine computed them (inputs first). <b>LCM applied</b>: the LCM that group rate was multiplied by (Property applies one per coverage group; ISO and technical apply the one record LCM to every group). Red ISO value: technical and ISO differ there. Highlighted deviated value: the filing changed it. "Written by" is the ERC rule file (and the tables read just before) that wrote the technical value.</div>')+'</div>';
  const q=document.getElementById('ws-q');q.oninput=()=>{WS.q=q.value;const pos=q.selectionStart;wsDraw();const n=document.getElementById('ws-q');n.focus();n.setSelectionRange(pos,pos);};}
// ---- the worksheet's Formula view: how each premium was computed, step by step, with the actual factors (console.formula)
function fxNum(v,isPrem){const n=Number(v);if(v===null||v===undefined||v===''||!isFinite(n))return esc(String(v??'—'));
  return isPrem?n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}):(Math.abs(n)>=1000?n.toLocaleString('en-US'):esc(String(v)));}
function fxIsPrem(t){return /premium/i.test(t.name||'');}
function fxChg(t){return t.tech!==undefined&&t.tech!==null&&Number(t.tech)!==Number(t.value);}
function fxTerm(t){return '<span class="fx-t'+(t.affected?' fx-aff':'')+'" title="'+esc(t.detail||t.source||'')+'">'+
  (fxChg(t)?'<s class="fx-was" title="technical">'+fxNum(t.tech,fxIsPrem(t))+'</s> → ':'')+'<b>'+fxNum(t.value,fxIsPrem(t))+'</b> '+esc(t.name)+'</span>';}
function fxTrio(f){const P=fxIsPrem(f),c=(k,l)=>f[k]!==undefined&&f[k]!==null?'<span class="fx-3"><i>'+l+'</i> '+fxNum(f[k],P)+'</span>':'';
  return c('tech','Technical')+c('iso','ISO')+c('dev','Deviated');}
function fxTechEq(f){if(f.dev===undefined||f.tech===undefined||Number(f.tech)===Number(f.dev))return '';
  if(!f.checks||f.step||f.op==='Mixed'||!f.terms.every(t=>t.tech!==undefined))return '<div class="mx-msg">Technical: '+fxNum(f.tech,fxIsPrem(f))+'</div>';
  const op=f.op==='Sum'?' + ':' × ';
  return '<div class="fx-eq fx-tech"><i>Technical</i> = '+f.terms.map(t=>fxNum(t.tech,fxIsPrem(t))).join(op)+(f.scale?' '+esc(f.scale):'')+' = '+fxNum(f.tech,fxIsPrem(f))+'</div>';}
function fxEq(f){const op=f.op==='Sum'?' + ':' × ';
  if(!f.checks)return '<div class="fx-eq fx-no">Computed from: '+f.terms.map(fxTerm).join(', ')+'<div class="mx-msg">'+esc(f.note||'')+'</div></div>';
  if(f.note&&f.exact==='0')return '<div class="fx-eq">= '+f.terms.map(fxTerm).join('')+' <span class="mx-msg">'+esc(f.note)+'</span></div>';
  let terms=f.terms.map(fxTerm);
  if(f.step){const ids=new Set(f.step.ids),inner=f.terms.filter(t=>ids.has(t.id)).map(fxTerm),rest=f.terms.filter(t=>!ids.has(t.id)).map(fxTerm);
    terms=['( '+inner.join(' × ')+' <span class="mx-msg">→ '+esc(f.step.value)+'</span> )'].concat(rest);}
  let h='<div class="fx-eq">= '+terms.join('<span class="fx-op">'+op+'</span>')+(f.scale?'<span class="fx-op"> '+esc(f.scale)+'</span>':'');
  if(f.rounded)h+='<span class="fx-op"> = </span>'+esc(f.exact)+' <span class="mx-msg">rounded to '+fxNum(f.value,fxIsPrem(f))+'</span>';
  h+='</div>';
  if(f.step)h+='<div class="mx-msg">'+esc(f.step.note)+'</div>';
  if((f.neutral||[]).length)h+='<div class="mx-msg">Also × 1.000 (no effect here): '+f.neutral.map(x=>esc(x.name)).join(', ')+'</div>';
  if(f.zeroNote)h+='<div class="mx-msg">'+esc(f.zeroNote)+'</div>';
  if(f.op==='Sum'&&(f.omitted||[]).length)h+='<div class="mx-msg">'+f.omitted.length+' other item'+(f.omitted.length>1?'s are':' is')+' 0 here and left out.</div>';
  return h;}
function fxSrc(f){const leaves=f.terms.filter(t=>!t.op&&t.source&&t.source!=='formula');if(!leaves.length)return '';
  return '<ul class="fx-src">'+leaves.map(t=>'<li'+(t.affected?' class="fx-aff"':'')+'>'+esc(t.name)+' <b>'+fxNum(t.value,fxIsPrem(t))+'</b> <span class="mx-msg">· '+
    esc(({input:'from the request',table:'',filing:'carrier filing',constant:'set by the rule',rule:''})[t.source]??'')+(t.detail&&t.source!=='input'?(t.source==='table'?'':' ')+esc(t.detail):'')+'</span></li>').join('')+'</ul>';}
function fxNode(f,depth){if(!f.op)return '';
  const head='<span class="fx-n'+(f.affected?' fx-aff':'')+'">'+esc(f.name)+'</span>'+(f.item&&depth>0?' <span class="mx-msg">'+esc(f.item)+'</span>':'')+' '+fxTrio(f);
  if(f.seeAbove)return '<div class="fx-leaf">'+head+' <span class="mx-msg">(computed above)</span></div>';
  const kids=f.terms.filter(t=>t.op&&!t.seeAbove);
  return '<details class="fx"'+(depth<2?' open':'')+'><summary>'+head+'</summary>'+fxEq(f)+fxTechEq(f)+fxSrc(f)+kids.map(k=>fxNode(k,depth+1)).join('')+
    f.terms.filter(t=>t.op&&t.seeAbove).map(k=>fxNode(k,depth+1)).join('')+'</details>';}
function fxPanel(d,hasDev){const side='both',got=WS.fx[side];
  if(!d.graph)return '<div class="mx-empty">No rating graph for this worksheet: open it again.</div>';
  if(!got){WS.fx[side]={loading:true};wbJSON('/api/console/workbench/formula',{token:d.graph,side}).then(j=>{WS.fx[side]=j;if(WS.view==='formula')wsDraw();})
    .catch(e=>{WS.fx[side]={error:String(e)};wsDraw();});}
  const tog='<div class="mx-msg" style="margin-top:6px">'+(hasDev?'Each line: <b>Technical</b> (pure ISO, our engine) · <b>ISO</b> (its answer, where it was asked) · <b>Deviated</b> ('+esc(d.company)+'). The formula is the deviated one; a factor the filing changed shows technical\u2019s value struck through, then the deviated value, and the line underneath gives technical\u2019s own arithmetic.':
    'Each line: <b>Technical</b> (our engine) · <b>ISO</b> (its answer, where it was asked). Pick a writing company to add <b>Deviated</b>.')+'</div>';
  const g=WS.fx[side];
  const body=!g||g.loading?'<div class="mx-msg">Working out the formulas…</div>':g.error?'<div class="mx-empty">'+esc(g.error)+'</div>':fxNode(g.root,0);
  return tog+'<div class="fx-wrap">'+body+'</div><div class="mx-msg">Each line is the arithmetic the engine did, with the values it used, and is shown only when that arithmetic reproduces the engine’s own figure (to the rule’s rounding). Click a line to open or close it. Hover a factor for the table row it came from.'+
    (hasDev?' Highlighted: reached by the carrier’s filing.':'')+' “Computed from” means the rule combines those inputs in a way this view doesn’t reconstruct.</div>';}
function wsCSV(){const d=WS.d,hasDev=!!d.company,qq=v=>v===null||v===undefined?'':'"'+String(v).replace(/"/g,'""')+'"';
  const head=['Section','Record','Field','Technical','ISO'].concat(hasDev?['Deviated']:[]).concat(['Technical vs ISO','Changed by deviations','Written by','Tables']);
  const rank={};(d.sections||[]).forEach((sc,i)=>sc.paths.forEach((p,j)=>{rank[p]=[i,j];}));
  const shown=wsShown().slice().sort((a,b)=>{const x=rank[a.path]||[1e9,0],y=rank[b.path]||[1e9,0];return x[0]-y[0]||x[1]-y[1];});
  const lines=[head.map(qq).join(',')].concat(shown.map(r=>{const m=v=>isPrem(r)?money(v):v;return [r.sectionLabel||'',r.record,r.label||r.field,m(r.technical),m(r.iso)].concat(hasDev?[m(r.deviated)]:[])
    .concat([r.techIso===null?'':r.techIso?'agree':'differ',hasDev?(r.changed?'yes':'no'):'',r.rule,(r.tables||[]).join('; ')]).map(qq).join(',');}));
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
  const fs=t.closest('[data-fxs]');if(fs){WS.fxSide=fs.dataset.fxs;wsDraw();return;}
  const rc=t.closest('[data-rec]');if(rc){const k=rc.dataset.rec;WS.shut.has(k)?WS.shut.delete(k):WS.shut.add(k);wsDraw();}});
function upSide(){
  if(WS.why){document.getElementById('up-side').innerHTML=wyHtml(WS.why);return;}
  const sx=UP.sel&&UP.rows.find(x=>x.id===UP.sel&&x.r&&x.r.carrier);
  if(sx){document.getElementById('up-side').innerHTML=upDev(sx);return;}
  const R=UP.rows.filter(x=>x.r).map(x=>x.r),both=R.filter(r=>r.stored&&r.stored.outcome==='rated'&&r.outcome==='rated');
  const agree=both.filter(r=>Number(r.premium)===Number(r.stored.iso)).length;
  const k=(t,v)=>'<tr><td>'+t+'</td><td style="text-align:right">'+v+'</td></tr>';
  document.getElementById('up-side').innerHTML='<div class="cap2">This list</div><table>'+k('Requests',UP.rows.length)+k('Priced by our engine',R.filter(r=>r.outcome==='rated').length)+
    k('ISO answered',R.filter(r=>r.stored).length)+k('Same price as ISO',agree)+k('Different from ISO',both.length-agree)+k('Not asked yet',upNeeds().length)+
    k('Could not be read',UP.rows.filter(x=>x.err).length)+'</table>'+
    '<div class="cap2">What the words mean</div><dl class="up-gl"><dt>Our price</dt><dd>Our engine, using ISO&#39;s rules as filed. Always free.</dd>'+
    '<dt>ISO&#39;s price</dt><dd>ISO&#39;s own answer to exactly the same request. Each answer is kept, so it counts as evidence and shows in Trace Diff.</dd>'+
    '<dt>With company</dt><dd>Our price after the writing company&#39;s filed changes (its deviations). Click it to see each change. Never sent to ISO.</dd>'+
    '<dt>What costs a call</dt><dd>Only &ldquo;Yes, ask ISO&rdquo;, one call per request.</dd></dl>'+
    '<div class="mx-msg">For specialists: priced with strict ERC and ROUND_HALF_UP, as the Workbench does. For another mode use <a href="/">the rating page</a>.</div>';
}
function upSendDialog(rows){
  const need=rows,el=document.getElementById('up-confirm');if(!need.length)return;
  const again=need.filter(x=>x.r.stored).length;
  fetch('/api/console/cap').then(r=>r.json()).then(c=>{
    const ad=c.lanes.find(l=>l.key==='adhoc'),room=Math.max(0,Math.min(ad.cap-ad.used,c.left)),over=need.length>room,n=need.length,pl=n>1?'s':'';
    const li=x=>'<li><b>'+esc(x.name)+'</b>: '+(x.r.stored?'ISO answered on '+esc((x.r.stored.stored_at||x.r.stored.date||'').slice(0,10))+'. The new answer replaces it; the old one stays in history.':'not asked yet.')+'</li>';
    el.innerHTML='<div class="up-cf'+(over?' full':'')+'"><h3>Ask ISO about '+n+' request'+pl+'?</h3>'+
      '<ul>'+need.slice(0,8).map(li).join('')+(n>8?'<li>and '+(n-8)+' more</li>':'')+'</ul>'+
      '<div>This uses <b>'+n+' ISO call'+pl+'</b>, one at a time, each recorded. Only the plain ISO version is sent; a writing company&#39;s version never leaves our engine.</div>'+
      '<div class="mx-msg">One-off calls today: '+ad.used+' of '+ad.cap+' used · '+c.left+' of '+c.cap+' left in all'+(over?' · <b>'+(n-room)+' would go past today&#39;s limit</b>, so they need a reason, recorded with each.':'')+'</div>'+
      '<div class="td-tools">'+(over?'<input id="up-reason" placeholder="Reason for going past today&#39;s limit">':'')+'<button class="btn primary" id="up-go">Yes, ask ISO · '+n+' call'+pl+'</button><button class="btn" id="up-cancel">Not now</button></div><div class="mx-msg" id="up-cmsg"></div></div>';
    el.scrollIntoView({block:'nearest'});
    document.getElementById('up-cancel').onclick=()=>{el.innerHTML='';};
    document.getElementById('up-go').onclick=()=>{const rs=document.getElementById('up-reason'),why=rs?rs.value.trim():'';
      if(over&&!why){document.getElementById('up-cmsg').textContent='Add a reason to go past the daily limit.';return;}
      el.innerHTML='';upSend(need,why,!!again);};});
}
async function upSend(rows,why,fresh){
  UP.busy=true;const msg=document.getElementById('up-msg');let sent=0,reused=0,stop='';
  for(const row of rows){
    row.busy='sending';upDraw();msg.textContent='Asking ISO: '+(sent+reused+1)+' of '+rows.length+'…';
    let j;try{j=await wbJSON('/api/console/workbench/upload-send',{text:row.text,index:row.index,reuse:!fresh,override:why,company:(row.r&&row.r.company)||''});}catch(e){j={error:String(e)};}
    row.busy='';
    if(j.error){stop=(j.capped?'Stopped at the cap: ':'Stopped: ')+j.error;upDraw();break;}
    j.reused?reused++:sent++;row.r.stored=j.stored;upDraw();}
  UP.busy=false;fetch('/api/console/cap').then(r=>r.json()).then(drawCap);
  msg.textContent=(stop?stop+' · ':'Done: ')+sent+' call'+(sent===1?'':'s')+' spent'+(reused?', '+reused+' answered from the store':'')+'.';
  upDraw();
}
function upItem(x){const v=JSON.parse(x.text);return JSON.stringify(Array.isArray(v)?v[x.index]:v,null,1);}
// a row's Download: a .zip with input.json and output.json for our engine, RaaS (ISO's stored request and response;
// what it would be sent when not asked) and, with a company, deviated, plus summary.json -- rated afresh on the
// server (free, never asks ISO)
function upDownload(x){const r=x.r,co=(r&&r.company)||'',base=(r?r.line+'-'+r.state+(x.gen?'':'-'+x.name.replace(/\.json.*$/i,'')):x.name.replace(/\.json.*$/i,''))+(co?'-'+co:'');
  const save=(t,n,ty)=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([t],{type:ty||'application/json'}));a.download=n;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
  if(!r){save(x.list?upItem(x):x.text,base+'.json');return;}
  wbJSON('/api/console/workbench/download',{text:x.text,index:x.index,company:co,policyType:UP.pt||'New'})
    .then(j=>{if(j.error)throw new Error(j.error);save(Uint8Array.from(atob(j.zip),c=>c.charCodeAt(0)),base+'.zip','application/zip');})
    .catch(e=>{document.getElementById('up-msg').textContent='Download failed: '+e.message;});}
function upEdit(x){const d=document.querySelector('.up-paste'),t=document.getElementById('up-text');d.open=true;t.value=x.list?upItem(x):x.text;
  UP.editName='Edited '+x.name.replace(/^(Generated|Edited) /,'');t.focus();t.setSelectionRange(0,0);t.scrollTop=0;t.scrollIntoView({block:'center'});}
function upGenStates(){const lob=document.getElementById('up-lob').value,sel=document.getElementById('up-state');
  const go=s=>{UP.spec[lob]=s;sel.innerHTML='<option value="*">All states ('+s.states.length+')</option>'+s.states.map(x=>'<option'+(x==='OH'?' selected':'')+'>'+x+'</option>').join('');};
  UP.spec[lob]?go(UP.spec[lob]):fetch('/api/console/workbench/spec?lob='+lob).then(r=>r.json()).then(go);}
function upGen(){const lob=document.getElementById('up-lob').value,st=document.getElementById('up-state').value,spec=UP.spec[lob],added=[];if(!spec)return Promise.resolve(added);
  return (st==='*'?spec.states:[st]).reduce((q,s)=>q.then(()=>fetch('/api/console/workbench/generate?lob='+lob+'&state='+s).then(r=>r.json()).then(j=>{
    if(j.error){UP.rows.push({id:++UP.seq,name:'Generated '+lob+' '+s,err:j.error});upDraw();return;}
    upAdd('Sample: '+(lob==='GL'?'General Liability':'Property')+', '+(BOOT.names[s]||s),j.text).forEach(x=>{x.gen=true;added.push(x);});})),Promise.resolve()).then(()=>added);}
function upFiles(files){[...files].forEach(f=>f.text().then(t=>upAdd(f.name,t)));}
(function(){const d=document.getElementById('up-drop'),f=document.getElementById('up-file');
  f.onchange=()=>{upFiles(f.files);f.value='';};
  ['dragenter','dragover'].forEach(e=>d.addEventListener(e,ev=>{ev.preventDefault();d.classList.add('over');}));
  ['dragleave','drop'].forEach(e=>d.addEventListener(e,ev=>{ev.preventDefault();d.classList.remove('over');}));
  d.addEventListener('drop',ev=>upFiles(ev.dataTransfer.files));
  const paste=()=>{const t=document.getElementById('up-text');if(!t.value.trim()){t.focus();return null;}const rs=upAdd(UP.editName||'Pasted request',t.value);t.value='';UP.editName='';return rs;};
  document.getElementById('up-add').onclick=paste;
  document.getElementById('up-add-cmp').onclick=()=>{const rs=paste();upCompare(rs||undefined);};
  document.getElementById('up-send').onclick=()=>upCompare();
  document.getElementById('up-gen-cmp').onclick=()=>{if(UP.busy){upCompare();return;}upGen().then(rs=>upCompare(rs));};
  document.getElementById('up-clear').onclick=()=>{if(UP.busy)return;UP.rows=[];document.getElementById('up-msg').textContent='';document.getElementById('up-confirm').innerHTML='';upDraw();};
  document.getElementById('up-out').addEventListener('click',ev=>{const dv=ev.target.closest('[data-dv]');
    if(dv){UP.sel=Number(dv.dataset.dv);upDraw();return;}
    const ws=ev.target.closest('[data-ws]');if(ws){const x=UP.rows.find(r=>String(r.id)===ws.dataset.ws);if(x)wsOpen(x);return;}
    const dl=ev.target.closest('[data-dl]'),ed=ev.target.closest('[data-ed]');
    if(dl||ed){const x=UP.rows.find(r=>String(r.id)===(dl||ed).dataset[dl?'dl':'ed']);if(x)(dl?upDownload:upEdit)(x);return;}
    const ag=ev.target.closest('[data-again]');
    if(ag){const x=UP.rows.find(r=>String(r.id)===ag.dataset.again);if(x)upCompare([x]);return;}
    const b=ev.target.closest('[data-x]');if(!b||UP.busy)return;UP.rows=UP.rows.filter(x=>String(x.id)!==b.dataset.x);upDraw();});
  document.getElementById('up-lob').onchange=upGenStates;
  document.getElementById('up-company').onchange=upRerate;document.getElementById('up-pt').onchange=upRerate;
  document.getElementById('up-side').addEventListener('click',ev=>{if(ev.target.closest('[data-unsel]')){UP.sel=null;upDraw();}});
  upCompanies();
  document.getElementById('up-gen').onclick=()=>{upGen();};
  upGenStates();upSide();})();
"""

# ---- P4: the Deviations Proof board ---------------------------------------------------------------------------------
# T1-T10 of DEVIATIONS-PLAN.md as rows, each from the last run of the suite that proves it (`console.deviations_proof`);
# T3 and T8 list every case ISO answered, each linked into Trace Diff. Nothing here rates or spends a call.

PROOF_HTML = """<section class="screen" id="s-proof" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Deviations Proof</div><h1>Can we trust the carriers' changes?</h1></div>
    <p>When we price for a carrier, we layer its filed changes on top of ISO's price. Each row is a promise that layering
    has to keep, read from the last run of the tests that check it. ISO itself only ever sees the standard request.
    Click a row for its checks, and for T3 the requests ISO answered, each opening in Trace Diff.</p></div>
  <div class="mx-stats" id="pf-stats"></div>
  <div id="pf-out"><div class="mx-loading">Loading…</div></div>
</div><aside class="mx-side" id="pf-side" aria-live="polite"></aside></div></section>"""

BUILT["proof"] = PROOF_HTML

PROOF_CSS = """
.pf-tbl{width:100%;border-collapse:collapse;font-size:14px;margin-top:10px}
.pf-tbl th{text-align:left;font-weight:600;font-size:12.5px;color:var(--color-neutral-700);padding:6px 10px}
.pf-tbl td{padding:11px 10px;border-top:1px solid var(--color-divider);vertical-align:top}
.pf-tbl tr{cursor:pointer}.pf-tbl tr.sel td{background:var(--color-accent-100)}
.pf-tbl .v{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.pf-cases td,.pf-checks td{padding:6px 8px;font-size:13px;border-top:1px solid var(--color-divider)}
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
  <div class="mx-head"><div><div class="eyebrow">Carrier Filings</div><h1>How each insurer prices differently from ISO</h1></div>
    <p>Insurers file their own changes to ISO's rates with each state. See at a glance who has filed where and how far
    each one moves a premium, test that it works as filed, then open a filing for the detail. Changes always sit on top
    of ISO's rates in force on the policy date.</p>
    <div class="td-tools"><label class="td-chk" for="fl-carrier">Carrier <select id="fl-carrier"><option value="">All carriers</option></select></label>
      <label class="td-chk fl-swl"><input type="checkbox" class="pl-sw" id="fl-tech"> Technical details</label></div></div>
  <div id="fl-up"></div>
  <div class="fl-sum" id="fl-sum"></div>
  <div class="fl-bar"><div class="bd-views" id="fl-views" role="tablist" aria-label="View">
      <button role="tab" data-v="filings">Filings</button><button role="tab" data-v="companies">Companies</button><button role="tab" data-v="timeline">Timeline</button></div>
    <div class="fl-runall"><button class="btn" id="fl-runall">Run the quick checks on every filing</button><span class="mx-msg" id="fl-runmsg">On our engine. No ISO calls.</span></div></div>
  <div class="fl-panel" id="fl-board"><div class="mx-loading">Loading…</div></div>
  <div class="fl-panel" id="fl-entry" hidden></div>
</div><aside class="mx-side" id="fl-side" aria-live="polite"></aside></div>
<input type="file" id="fl-file" accept=".zip" hidden></section>"""

BUILT["filings"] = FILINGS_HTML

FILINGS_CSS = """
#s-filings [hidden]{display:none!important}
.fl-swl{display:inline-flex;gap:8px;align-items:center}
.fl-sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px}
.fl-sum div{background:var(--color-panel);border-radius:var(--radius-md);padding:14px 16px}
.fl-sum b{display:block;font:400 28px/1.15 var(--font-heading)}
.fl-sum span{font-size:13.5px;color:var(--color-neutral-700)}
.fl-bar{display:flex;gap:12px 20px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.fl-runall{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.fl-panel{background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-lg);padding:22px 24px;display:flex;flex-direction:column;gap:16px;min-width:0}
.fl-panel h2{margin:0;font:400 23px/1.2 var(--font-heading)}
.fl-panel h3{margin:0;font:500 17px var(--font-heading)}
.fl-x{display:inline-block;border-radius:var(--radius-pill);padding:2px 10px;font-weight:600;font-size:13.5px;white-space:nowrap}
.fl-h0{background:var(--teal-soft)}.fl-h1{background:#efe3b4}.fl-h2{background:#e9d491}.fl-h3{background:#f6b48f}.fl-h4{background:#f58a63}
.fl-key{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--color-neutral-700)}
.fl-key i{display:inline-block;width:12px;height:12px;border-radius:4px;vertical-align:-1px;margin-right:6px}
.fl-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.fl-fc{border:1px solid var(--color-divider);border-radius:var(--radius-lg);background:var(--color-bg);padding:16px 18px;display:flex;flex-direction:column;gap:12px;cursor:pointer;text-align:left;font:inherit;color:inherit}
.fl-fc:hover{background:var(--color-accent-100)}
.fl-fc.on{background:var(--color-card);border-color:var(--color-text);box-shadow:inset 0 0 0 1px var(--color-text)}
.fl-fc .t{font:500 19px/1.25 var(--font-heading)}
.fl-fc .co{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 10px;align-items:center;font-size:14px}
.fl-prog{display:flex;gap:3px}.fl-prog i{flex:1;height:6px;border-radius:var(--radius-pill);background:var(--color-divider)}.fl-prog i.d{background:var(--teal-hover)}
.fl-tchip{font-size:12.5px;border-radius:var(--radius-pill);padding:2px 10px;background:var(--teal-soft);width:fit-content}
.fl-tchip.no{background:var(--ox-tint)}.fl-tchip.wait{background:var(--color-panel)}
.fl-tag{font-size:12px;color:var(--color-neutral-700);border:1px solid var(--color-divider);border-radius:var(--radius-pill);padding:0 8px;margin-left:4px;white-space:nowrap}
.fl-cg{border-collapse:separate;border-spacing:6px;font-size:14px;min-width:560px}
.fl-cg th{font-weight:600;font-size:13px;color:var(--color-neutral-700);text-align:left;padding:0 4px;vertical-align:bottom}
.fl-cg td.c{border-radius:var(--radius-md);padding:10px 12px;cursor:pointer;min-width:150px;vertical-align:top}
.fl-cg td.c:hover,.fl-cg td.c.on{outline:2px solid var(--color-text);outline-offset:1px}
.fl-cg td.c b{font:400 22px/1.1 var(--font-heading);display:block}
.fl-cg td.c small,.fl-cg td.nm small{display:block;font-size:12.5px;color:var(--color-neutral-700)}
.fl-cg td.iso{background:var(--color-panel);color:var(--color-neutral-700);border-radius:var(--radius-md);padding:10px 12px;font-size:13px}
.fl-cg td.nm b{font:500 16px var(--font-heading)}
.fl-tl{display:grid;grid-template-columns:210px minmax(0,1fr);gap:12px 16px;align-items:center;min-width:620px;font-size:14px;padding-bottom:22px}
.fl-tl .ax{display:flex;justify-content:space-between;font-size:12.5px;color:var(--color-neutral-700);border-bottom:1px solid var(--color-divider);padding-bottom:4px}
.fl-tl .lane{position:relative;height:30px;background:var(--color-panel);border-radius:var(--radius-pill);margin-bottom:18px}
.fl-tl .lane i{position:absolute;top:5px;height:20px;border-radius:var(--radius-pill)}
.fl-tl .lane i.n{background:var(--teal-mid,#8ee9c8)}.fl-tl .lane i.r{background:var(--teal-hover)}
.fl-tl .lane span{position:absolute;top:34px;font-size:12px;color:var(--color-neutral-700);white-space:nowrap}
.fl-tl .nm{cursor:pointer}.fl-tl .nm:hover b{text-decoration:underline}
.fl-tl .nm b{font:500 15px var(--font-heading);display:block}.fl-tl .nm small{color:var(--color-neutral-700);font-size:12.5px}
.fl-fhead{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:flex-start;justify-content:space-between}
.fl-steps{display:flex;gap:6px;flex-wrap:wrap}
.fl-steps span{font-size:13px;padding:4px 12px;border-radius:var(--radius-pill);background:var(--color-panel);color:var(--color-neutral-700)}
.fl-steps span.done{background:var(--teal-soft);color:var(--color-text)}
.fl-steps span.now{background:var(--color-text);color:var(--color-bg);font-weight:600}
.fl-tabs{display:flex;gap:4px;flex-wrap:wrap;border-bottom:1px solid var(--color-divider)}
.fl-tabs button{font:500 14.5px var(--font-body);border:0;background:none;color:var(--color-neutral-700);padding:9px 14px;border-bottom:2px solid transparent;cursor:pointer}
.fl-tabs button[aria-selected="true"]{color:var(--color-text);border-bottom-color:var(--color-text)}
.fl-short{font-size:16px;line-height:1.6;max-width:76ch;margin:0}
.fl-big{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.fl-big div{border-radius:var(--radius-md);padding:14px 16px;background:var(--color-panel)}
.fl-big b{font:400 32px/1.1 var(--font-heading);display:block}
.fl-big span{font-size:13.5px;color:var(--color-neutral-700)}
.fl-mdw{overflow-x:auto}
.fl-md{width:100%;border-collapse:collapse;font-size:14px;margin:4px 0}
.fl-md th{text-align:left;font-weight:600;font-size:13px;color:var(--color-neutral-700);padding:6px 10px}
.fl-md td{padding:9px 10px;border-top:1px solid var(--color-divider);text-align:left;vertical-align:top}
.fl-md td.v,.fl-md th.v{text-align:center}.fl-md .r{text-align:right;white-space:nowrap}
.fl-md tr.grp td{background:var(--color-panel);font-weight:600;font-size:13.5px;border-top:0}
.fl-md .nw{white-space:nowrap}
.fl-md small{display:block;font-size:12px;color:var(--color-neutral-700);font-weight:400}
.fl-eff{display:grid;grid-template-columns:minmax(120px,190px) minmax(0,1fr) 70px;gap:5px 12px;align-items:center;font-size:14px}
.fl-eff .bar{height:12px;background:var(--color-panel);border-radius:var(--radius-pill);position:relative;overflow:hidden}
.fl-eff .bar i{position:absolute;top:0;bottom:0;left:0;border-radius:var(--radius-pill)}
.fl-eff .p{text-align:right;font-weight:600}
.fl-eff .co{grid-column:1/-1;font:500 16px var(--font-heading);margin-top:12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.fl-eff .co:first-child{margin-top:0}
.fl-ck{border:1px solid var(--color-divider);border-radius:var(--radius-md);background:var(--color-bg);padding:14px 16px;display:grid;grid-template-columns:28px minmax(0,1fr) auto;gap:6px 12px;align-items:start}
.fl-ic{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-size:12.5px;font-weight:600;background:var(--teal-soft)}
.fl-ic.x{background:var(--ox-tint)}.fl-ic.o{background:var(--color-panel);color:var(--color-neutral-700)}
.fl-ck h4{margin:0;font:500 17px var(--font-heading)}
.fl-ck .res{font-weight:600;white-space:nowrap;font-size:14px}
.fl-ck .bd{grid-column:2/-1;display:flex;flex-direction:column;gap:8px;min-width:0}
.fl-cost{font-size:12.5px;background:var(--teal-soft);border-radius:var(--radius-pill);padding:2px 9px;white-space:nowrap}
.fl-cost.iso{background:var(--color-accent-100)}
input.fl-ex{width:88px;font:inherit;font-size:14px;border:1px solid var(--color-divider);border-radius:8px;padding:4px 8px;text-align:right;background:var(--color-card)}
.fl-ref{background:var(--color-panel);border-radius:var(--radius-sm);padding:10px 12px;font-size:14px}
.fl-out{background:var(--color-card);border-radius:var(--radius-md);border:1px solid var(--color-divider);padding:10px 14px;font-size:14px}
.fl-trail{display:flex;flex-direction:column}
.fl-trail .it{display:grid;grid-template-columns:28px minmax(0,1fr);gap:10px;padding:12px 0;border-top:1px solid var(--color-divider)}
.fl-trail .it:first-child{border-top:0}
.fl-doc{padding:6px 0;font-size:14px;overflow-wrap:anywhere}
.fl-entry h4{margin:14px 0 4px;font-size:14px}.fl-entry p{margin:6px 0}.fl-entry ul{margin:4px 0;padding-left:18px}
.fl-entry code,.fl-tech{overflow-wrap:anywhere}
.fl-tech{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--color-neutral-700)}
details.fl-more summary{cursor:pointer;color:var(--color-neutral-700);font-size:13.5px}
.fl-drop{border:1.5px dashed var(--color-accent-300,#c2b893);border-radius:var(--radius-md);padding:14px;text-align:center;font-size:14px;color:var(--color-neutral-700);background:var(--color-card);cursor:pointer}
.fl-drop.over{background:var(--teal-soft)}
.fl-howto{margin:0;padding-left:20px;font-size:14px;display:grid;gap:4px}
.fl-gl dt{font-weight:600;font-size:13.5px;margin-top:8px}.fl-gl dd{margin:2px 0 0;font-size:13.5px;color:var(--color-neutral-700)}
.fl-card{border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:12px 14px;background:var(--color-card)}
"""

FILINGS_JS = r"""
const FL={d:null,b:null,sel:null,tab:'short',tech:false,up:null,carrier:'',view:'filings',t:{},st:null,poll:null,iso:{},isoAsk:false,tryK:null,full:false};
// the carrier picker and the view: '' is every carrier; remembered per viewer, quietly, where the browser allows it
try{FL.carrier=localStorage.getItem('fl-carrier')||'';FL.view=localStorage.getItem('fl-view')||'filings';}catch(e){}
function flMine(x){return !FL.carrier||x.carrier===FL.carrier;}
function flFilings(){return FL.d?FL.d.filings.filter(flMine):[];}
const FL_COV={'Premises/Operations':'Premises','Products/Completed Ops':'Products','Group I':'Fire & lightning','Group II':'Wind & hail',
  'Broad':'Broad form','Special':'Special form','Earthquake':'Earthquake'};
const FL_GLOSS=[['ISO','Insurance Services Office: publishes the standard rates, rules and forms most US commercial insurers start from.'],
  ['Rate filing','An insurer\u2019s request, approved by the state, to charge differently from ISO.'],
  ['Loss cost multiplier','The factor an insurer applies to ISO\u2019s rates. 1.10 means 10% above ISO; 0.94 means 6% below.'],
  ['Class','ISO\u2019s code for the kind of business, such as a retail store or a contractor.'],
  ['Class group','A set of kinds of business that share one factor in a filing.'],
  ['\u201ca\u201d-rated class','A specialty class ISO publishes no rate for; the insurer sets the rate itself.'],
  ['Effective dates','When a filing starts: one date for new policies, often a later one for renewals.'],
  ['Typical businesses','A set of sample risks we price both ways to estimate the effect. Not real customers.'],
  ['Technical price','Our price at ISO\u2019s own rates, with no insurer\u2019s changes. ISO is only ever asked about this one.']];
const FL_STEPS=['Received','Reviewed','Impact checked','In use','Proven'];
function flKey(f){return f.id||f.serff;}
function flChip(ok){return ok?'<span class="chip verified">✓</span> ':'<span class="chip mismatch">×</span> ';}
function flPct(v){return v==null||v===''?'—':(Number(v)>0?'+':Number(v)<0?'\u2212':'')+esc(String(Math.abs(Number(v))))+'%';}
function flHeat(v){v=Number(v);return v<0?'fl-h0':v<50?'fl-h1':v<100?'fl-h2':v<150?'fl-h3':'fl-h4';}
function flX(v){return v==null||v===''||isNaN(Number(v))?'<span class="mx-msg">—</span>':'<span class="fl-x '+flHeat(v)+'">'+flPct(v)+'</span>';}
function flCov(g){return esc(FL_COV[g]||g);}
function flSel(){return flFilings().find(x=>flKey(x)===FL.sel||x.serff===FL.sel);}
function flStates(f){return String(f.state||'').split(',').map(s=>s.trim()).filter(Boolean);}
function flDate(d){if(!d)return '';const x=new Date(String(d).slice(0,10)+'T12:00');return isNaN(x)?esc(d):x.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});}
function flCoName(f,c){const v=f.versions.find(x=>x.company===c);return (v&&v.plain&&v.plain.company)||((FL.b&&FL.b.companies.find(x=>x.code===c))||{}).name||c;}
function flShort(n){return String(n).replace(/ (Insurance )?(Company|& Casualty Company)$/,'').replace(/ Insurance$/,'');}
// the version of each company in use (its newest approved), else its newest proposal
function flLive(f){const out={};f.versions.forEach(v=>{const o=out[v.company],ap=v.status==='approved';
  if(!o||(ap&&(o.status!=='approved'||v.version>o.version))||(!ap&&o.status!=='approved'&&v.version>o.version))out[v.company]=v;});return out;}
// each company's headline: its effect in this filing's own state, against ISO
function flHead(f){const st=flStates(f),out={};(f.impacts||[]).filter(i=>!i.draft).forEach(i=>{const own=st.map(s=>(i.byState||{})[s]).filter(Boolean);
  const a=own.length===1?own[0]:i.all;if(a&&a.change!=null)out[i.company]=Number(a.change);});return out;}
function flDates(f){const n=f.versions.map(v=>v.new_eff).filter(Boolean).sort(),r=f.versions.map(v=>v.renewal_eff).filter(Boolean).sort();return {n:n[n.length-1]||'',r:r[r.length-1]||''};}
function flTested(f){const t=f.test;if(!t||!t.ranAt)return '<span class="fl-tchip no">Never tested here</span>';
  if(t.error)return '<span class="fl-tchip no">Last test stopped</span>';
  const ok=t.ok||{},bad=ok.factors===false||ok.effect===false;
  return '<span class="fl-tchip'+(bad?' no':'')+'">'+(bad?'× Last test found a problem':'✓ Tested')+' · '+flDate(t.ranAt)+'</span>';}
function flRunning(serff){const s=FL.st||{};return s.running&&s.running.serff===serff?s.running:(s.waiting||[]).includes(serff)?{state:'waiting'}:null;}
// ---- the high level
function flSumDraw(){const fs=flFilings(),el=document.getElementById('fl-sum');if(!fs.length){el.innerHTML='';return;}
  const cos=new Set(fs.flatMap(f=>Object.keys(flLive(f)))),sts=new Set(fs.flatMap(flStates)),all=fs.flatMap(f=>Object.values(flHead(f)));
  const inuse=fs.filter(f=>f.versions.some(v=>v.status==='approved')).length,tested=fs.filter(f=>f.test&&f.test.ranAt&&!f.test.error).length;
  const box=(b,t)=>'<div><b>'+b+'</b><span>'+t+'</span></div>';
  el.innerHTML=box(fs.length,'filing'+(fs.length===1?'':'s')+', '+inuse+' in use')+box(cos.size,'compan'+(cos.size===1?'y':'ies')+' in '+sts.size+' state'+(sts.size===1?'':'s'))+
    (all.length?box(flPct(Math.min(...all))+' to '+flPct(Math.max(...all)),'typical premium against ISO'):'')+
    box(tested+' of '+fs.length,tested===fs.length?'tested':'tested; '+(fs.length-tested)+' never tested');}
function flCardsDraw(){const fs=flFilings();
  return '<div><h2>What has each insurer filed?</h2><p class="mx-msg">One card per filing. The number is how far a typical premium moves against ISO for each company. Click a card to open it below.</p></div>'+
    '<div class="fl-cards">'+fs.map(f=>{const p=f.plain||{},h=flHead(f),lv=flLive(f),at=FL_STEPS.indexOf(p.step),d=flDates(f),run=flRunning(f.serff);
      return '<button class="fl-fc'+(flSel()===f?' on':'')+'" data-f="'+esc(flKey(f))+'"><div><div class="mx-msg">'+esc(p.carrier||f.carrier)+(FL.tech?' · SERFF '+esc(f.serff):'')+'</div><div class="t">'+esc((p.line||f.line)+' · '+(p.state||f.state))+'</div></div>'+
        '<div class="co">'+Object.keys(lv).map(c=>'<span>'+esc(flShort(flCoName(f,c)))+(lv[c].status!=='approved'?'<span class="fl-tag">proposal</span>':'')+'</span>'+flX(h[c])).join('')+'</div>'+
        '<div><div class="fl-prog">'+FL_STEPS.map((s,i)=>'<i class="'+(i<=at?'d':'')+'"></i>').join('')+'</div><span class="mx-msg">'+esc(p.step||'')+(d.n?' · new policies from '+flDate(d.n):'')+'</span></div>'+
        (run?'<span class="fl-tchip wait">'+(run.state==='waiting'?'Waiting to test':'Testing… '+(run.done||0)+' of '+(run.total||'…'))+'</span>':flTested(f))+'</button>';}).join('')+'</div>';}
// the companies view (B-20's filings board): each company against each line and state, shaded by its effect
function flBoard(){const el=document.getElementById('fl-board'),b=FL.b;if(!b||!FL.d)return;
  document.querySelectorAll('#fl-views button').forEach(x=>x.setAttribute('aria-selected',x.dataset.v===FL.view));
  const fs=flFilings();
  if(!fs.length){el.innerHTML='<div class="mx-empty">'+(FL.carrier?'No filings yet for this carrier.':'No filings yet. Upload a filing packet to start.')+'</div>';return;}
  if(FL.view==='timeline'){el.innerHTML=flTimeline(fs);return;}
  if(FL.view!=='companies'){el.innerHTML=flCardsDraw();return;}
  const cells=b.cells.filter(flMine),key=c=>c.line+'|'+c.state,cols=b.columns.filter(c=>cells.some(x=>key(x)===key(c))),cos=b.companies.filter(flMine),sel=flSel();
  const fOf=(co,col)=>fs.find(f=>f.line===col.line&&flStates(f).includes(col.state)&&f.versions.some(v=>v.company===co));
  el.innerHTML='<div><h2>Which company is dearest, and where?</h2><p class="mx-msg">Each company against each line and state, shaded by how far its typical premium sits from ISO. \u201cISO\u2019s rates\u201d means the company has no filing there. Click a box to open the filing.</p></div>'+
    '<div class="fl-key">'+[['fl-h0','Below ISO'],['fl-h1','Up to 50% above'],['fl-h2','50\u2013100% above'],['fl-h3','100\u2013150% above'],['fl-h4','150% or more above']].map(([c,l])=>'<span><i class="'+c+'"></i>'+l+'</span>').join('')+'</div>'+
    '<div class="fl-mdw"><table class="fl-cg"><tr><th></th>'+cols.map(c=>'<th>'+esc(c.plain||c.line+' · '+c.state)+'</th>').join('')+'</tr>'+
    cos.map(co=>'<tr><td class="nm"><b>'+esc(co.name||co.code)+'</b>'+(FL.tech?'<small>'+esc(co.code+(co.naic?' · NAIC '+co.naic:''))+'</small>':'')+'</td>'+cols.map(col=>{
      const c=cells.filter(x=>x.company===co.code&&key(x)===key(col)),f=fOf(co.code,col);
      if(!c.length)return '<td class="iso">ISO\u2019s rates</td>';
      const live=c.find(x=>x.status!=='draft'),v=f?flHead(f)[co.code]:null,draft=!live;
      const tip=FL.tech?c.map(x=>(x.filing||'')+' v'+(x.version||'')+' · '+x.status).join('\n'):'';
      return '<td class="c '+(v!=null?flHeat(v):'')+(f&&sel===f?' on':'')+'"'+(f?' data-f="'+esc(flKey(f))+'"':'')+(tip?' title="'+esc(tip)+'"':'')+'><b>'+(v!=null?flPct(v):draft?'Proposal':'In use')+'</b>'+
        '<small>'+(draft?'not in use yet':(live.plain&&live.plain.since?'since '+esc(live.plain.since):''))+'</small>'+(c.some(x=>(x.drafts||[]).length)?'<span class="fl-tag">proposal pending</span>':'')+'</td>';}).join('')+'</tr>').join('')+'</table></div>';}
function flTimeline(fs){const ds=fs.map(f=>({f,d:flDates(f)})).filter(x=>x.d.n);
  if(!ds.length)return '<div class="mx-empty">No effective dates yet.</div>';
  const t=s=>new Date(s+'T12:00').getTime(),lo=new Date(Math.min(...ds.map(x=>t(x.d.n))));lo.setDate(1);lo.setMonth(lo.getMonth()-1);
  const hi=new Date(Math.max(...ds.map(x=>t(x.d.r||x.d.n))));hi.setDate(1);hi.setMonth(hi.getMonth()+2);
  const x=s=>Math.max(0,Math.min(100,100*(t(s)-lo.getTime())/(hi.getTime()-lo.getTime())));const ms=[];
  for(const m=new Date(lo);m<=hi;m.setMonth(m.getMonth()+1))ms.push(m.toLocaleDateString('en-US',{month:'short'})+(m.getMonth()===0?' '+String(m.getFullYear()).slice(2):''));
  return '<div><h2>When does each filing take effect?</h2><p class="mx-msg">The light bar starts on the date for new policies, the dark bar on the date for renewals. Policies on or after these dates use the insurer\u2019s rates.</p></div>'+
    '<div class="fl-mdw"><div class="fl-tl"><div></div><div class="ax">'+ms.map(m=>'<span>'+m+'</span>').join('')+'</div>'+
    ds.map(({f,d})=>{const p=f.plain||{};return '<div class="nm" data-f="'+esc(flKey(f))+'"><b>'+esc((p.line||f.line)+' · '+(p.state||f.state))+'</b><small>'+esc(Object.keys(flLive(f)).map(c=>flShort(flCoName(f,c))).join(', '))+'</small></div>'+
      '<div class="lane"><i class="n" style="left:'+x(d.n)+'%;right:0"></i>'+(d.r?'<i class="r" style="left:'+x(d.r)+'%;right:0"></i>':'')+
      '<span style="left:'+x(d.n)+'%">new '+flDate(d.n)+'</span>'+(d.r?'<span style="left:'+Math.min(x(d.r),80)+'%">renewals '+flDate(d.r)+'</span>':'')+'</div>';}).join('')+'</div></div>';}
// ---- one filing: what changes, companies side by side (the version in use), each version in full folded below
function flRowNum(t){const m=/([\d.]+)% (above|below)/.exec(t||'');return m?(m[2]==='below'?-1:1)*Number(m[1]):null;}
function flRows(f){if(!f.versions.length)return '<div class="mx-msg">Nothing proposed yet.</div>';
  const lv=flLive(f),cs=Object.keys(lv),grid=new Map();
  cs.forEach(c=>{const v=lv[c];((v.plain||{}).rows||[]).forEach((r,i)=>{const k=r.where+'\u0001'+r.what;if(!grid.has(k))grid.set(k,{where:r.where,what:r.what,by:{}});grid.get(k).by[c]={r,d:(v.detail||[])[i]};});});
  const groups=[...new Set([...grid.values()].map(x=>x.where))],cg=groups.some(g=>/class group/i.test(g));
  const gname=g=>cg&&/^every class$/i.test(g)?'All other classes':g.charAt(0).toUpperCase()+g.slice(1);
  const cell=x=>{if(!x)return '<span class="mx-msg">—</span>';const n=flRowNum(x.r.change);
    return (n!=null?'<span class="fl-x '+flHeat(n)+'">'+esc(x.r.change)+'</span>':esc(x.r.change))+(FL.tech&&x.d?'<small>'+esc(x.d.mode+' '+x.d.value)+'</small>':'');};
  return '<div class="fl-mdw"><table class="fl-md"><tr><th>What</th>'+cs.map(c=>'<th class="v">'+esc(flCoName(f,c))+(lv[c].status!=='approved'?' <span class="fl-tag">proposal</span>':'')+'</th>').join('')+'</tr>'+
    groups.map(g=>'<tr class="grp"><td colspan="'+(cs.length+1)+'">'+esc(gname(g))+'</td></tr>'+[...grid.values()].filter(x=>x.where===g).map(x=>'<tr><td>'+esc(x.what)+'</td>'+cs.map(c=>'<td class="v">'+cell(x.by[c])+'</td>').join('')+'</tr>').join('')).join('')+'</table></div>'+
    '<div class="mx-msg">'+esc(Object.values(lv)[0]&&Object.values(lv)[0].plain&&Object.values(lv)[0].plain.starts||'')+'. '+(FL.tech?'Under each change: how it is applied and the filed value.':'Switch on technical details for the filed values.')+'</div>'+
    '<details class="fl-more"><summary>Each version in full ('+f.versions.length+')</summary>'+f.versions.map(v=>{const p=v.plain||{};return '<div class="fl-doc"><b>'+esc(p.company||v.company)+' · version '+esc(v.version)+'</b> <span class="mx-msg">'+esc(p.status||'')+'</span>'+
      '<div class="fl-mdw"><table class="fl-md"><tr><th>Coverage</th><th>Applies to</th><th>Change</th><th>Starts</th><th>Why</th></tr>'+
      (p.rows||[]).map(r=>'<tr><td class="nw">'+esc(r.what)+'</td><td>'+esc(r.where)+'</td><td class="nw"><b>'+esc(r.change)+'</b></td><td class="mx-msg">'+esc(r.starts||'')+'</td><td class="mx-msg">'+esc(r.note||'')+'</td></tr>').join('')+'</table></div>'+
      (FL.tech?'<div class="fl-tech">'+esc(v.filing+' v'+v.version+' · '+v.compiledKeys+' compiled keys')+'</div><div class="fl-mdw"><table class="fl-md"><tr><th>Target</th><th>Scope</th><th class="r">Value</th><th>Mode</th><th>Cite</th></tr>'+
        (v.detail||[]).map(r=>'<tr><td><code>'+esc(r.target)+'</code></td><td><code>'+esc(JSON.stringify(r.scope||{}))+'</code></td><td class="r">'+esc(r.value)+'</td><td>'+esc(r.mode)+'</td><td>'+esc(r.cite)+'</td></tr>').join('')+'</table></div>':'')+'</div>';}).join('')+'</details>';}
function flDraftImpact(f,v){return (f.impacts||[]).filter(x=>x.company===v.company&&x.draft===v.filing+'.v'+v.version).pop()||null;}
// the effect on premium: bars by type of business in this filing's own state, coloured by how far from ISO
function flImpact(f){const st=flStates(f);
  if(!f.impacts||!f.impacts.length)return '<div class="mx-msg">Not worked out yet. It runs on our own engine when a filing is uploaded or built.</div>';
  const one=st.length===1?st[0]:null,rows=[];let mx=1;
  const sets=f.impacts.map(i=>{const p=i.plain||{},own=one&&(i.byState||{})[one],a=own||i.all;
    let types=Object.entries(i.byRiskType||{}).map(([k,v])=>[k,Number(v.change)]);
    if(one&&Object.keys(i.byStateRiskType||{}).length)types=Object.entries(i.byStateRiskType).filter(([k])=>k.startsWith(one+' | ')).map(([k,v])=>[k.split(' | ')[1],Number(v.change)]);
    types.sort((x,y)=>y[1]-x[1]);types.forEach(([,v])=>mx=Math.max(mx,Math.abs(v)));if(a&&a.change!=null)mx=Math.max(mx,Math.abs(Number(a.change)));return {i,p,a,types};});
  return '<div class="fl-eff">'+sets.map(({i,p,a,types})=>'<div class="co">'+esc(p.company||i.company)+(i.draft?' <span class="fl-tag">proposal</span>':'')+' '+flX(a&&a.change)+
      (p.vsNow?' <span class="mx-msg">'+esc(p.vsNow)+' (vs today)</span>':'')+'</div>'+
      types.map(([k,v])=>'<span>'+esc(k)+'</span><div class="bar"><i class="'+flHeat(v)+'" style="width:'+(Math.abs(v)/mx*100).toFixed(1)+'%"></i></div><span class="p">'+flPct(v)+'</span>').join('')+
      (Object.keys((i.byCoverage||{}).All||{}).length?'<span class="mx-msg" style="grid-column:1/-1">By coverage'+(one&&Object.keys(i.states||{}).length>1?' (all its states together)':'')+': '+Object.entries(i.byCoverage.All).map(([g,c])=>flCov(g)+' '+flPct(c.change)).join(' · ')+'</span>':'')+
      (FL.tech?'<span class="fl-tech" style="grid-column:1/-1">'+esc((a?a.rated+' risks, '+flPct(a.min)+' to '+flPct(a.max)+' per risk · ':'')+i.file+' · '+(i.generated||''))+'</span>':'')).join('')+'</div>'+
    '<div class="mx-msg">Estimated by pricing typical businesses both ways, the insurer\u2019s rates against ISO\u2019s, on our own engine. Not real customers.</div>';}
function flProof(f){const p=f.proof;if(!p)return '';return p.ran?flChip(p.passed)+p.ok+' of '+p.checks+' checks':esc(p.suite)+' has not been run';}
function flSources(f){if(!f.sources.length)return '<div class="mx-msg">No documents saved.</div>';
  const all=f.sources.every(x=>x.intact);
  return '<b>'+(all?'Original documents, unchanged since we received them':'Some documents are missing or have changed since we received them')+'</b>'+
    f.sources.map(x=>'<div class="fl-doc">'+(x.present?'<a href="'+esc(x.url)+'" target="_blank" rel="noopener">'+esc(x.name)+'</a>':esc(x.name)+' <b>(missing)</b>')+
      (x.present&&!x.intact?' <b>(changed)</b>':'')+'<div class="mx-msg">'+esc(x.what)+'</div>'+(FL.tech?'<div class="fl-tech">SHA-256 '+esc(x.sha256||'')+'</div>':'')+'</div>').join('');}
function flHistory(f){const s=f.plain&&f.plain.historyShort;
  if(!f.entry)return '<div class="mx-msg">Not in the filings log yet.</div>';
  return (s?'<div class="mx-msg">'+esc(s)+'</div>':'')+'<details class="fl-more"'+(s?'':' open')+'><summary>The full log entry</summary><div class="fl-entry">'+f.entry+'</div></details>';}
function flTrail(f){const ic=(ok,c)=>'<span class="fl-ic'+(ok===false?' x':ok==null?' o':'')+'">'+c+'</span>',p=f.proof,t=f.test||{};
  return '<div class="fl-trail">'+
    '<div class="it">'+ic(p&&p.ran?p.passed:null,p&&p.ran?(p.passed?'✓':'×'):'–')+'<div><b>'+(p&&p.ran?'The proving suite: '+p.ok+' of '+p.checks+' automatic tests pass':'No proving suite recorded for this filing')+'</b>'+
      (p&&p.ran?'<div class="mx-msg">Last run '+flDate(p.ranAt)+(FL.tech?' · '+esc(p.suite)+' · '+esc(p.commit||''):'')+'</div>':'<div class="mx-msg">The quick checks on the Test it tab still work for it.</div>')+'</div></div>'+
    '<div class="it">'+ic(t.ranAt&&!t.error?!((t.ok||{}).factors===false||(t.ok||{}).effect===false):null,'⚑')+'<div><b>Quick checks</b><div class="mx-msg">'+(t.ranAt?'Last run '+flDate(t.ranAt)+' ('+esc(t.mode||'quick')+').':'Never run.')+' <a href="#" data-tab="test">Open Test it</a></div></div></div>'+
    (f.sheet?'<div class="it">'+ic(true,'✎')+'<div><b>Our review</b><div class="mx-msg">What was filed, how we built it, decisions and proof.</div><details class="fl-more"><summary>Read our review</summary><div class="fl-entry">'+f.sheet+'</div></details></div></div>':'')+
    '<div class="it">'+ic(true,'⌚')+'<div><b>History</b>'+flHistory(f)+'</div></div>'+
    '<div class="it">'+ic(f.sources.every(x=>x.intact),'▤')+'<div>'+flSources(f)+'</div></div></div>';}
// ---- Test it: quick checks on our engine, and an ISO spot check of the technical price (D21)
function flTest(f){const R=FL.t[f.serff],run=flRunning(f.serff),cos=Object.keys(flLive(f)),one=flStates(f).length===1;
  const ic=ok=>ok==null?'<span class="fl-ic o">–</span>':ok?'<span class="fl-ic">✓</span>':'<span class="fl-ic x">×</span>';
  const co=(c,st)=>esc(flCoName(f,c))+(one?'':' · '+esc(st));
  let h='<div class="td-tools" style="justify-content:space-between"><span class="mx-msg">'+(R&&R.ranAt?'Last run '+flDate(R.ranAt)+' on '+R.priced+' risk'+(R.priced===1?'':'s')+' ('+(R.mode==='full'?'the whole typical set':'one per class')+').':'Never run.')+
    ' The first two checks are free and use our engine only.</span><span class="td-tools"><label class="td-chk"><input type="checkbox" id="fl-full"'+(FL.full?' checked':'')+'> whole typical set (slower)</label>'+
    '<button class="btn primary" data-run="'+esc(f.serff)+'"'+(run?' disabled':'')+'>'+(run?'Testing…':R&&R.ranAt?'Run again':'Run the quick checks')+'</button></span></div>';
  if(run)h+='<div class="fl-out">'+(run.state==='waiting'?'Waiting for the test before it to finish.':'Pricing typical businesses with and without the filing on our engine… '+(run.done||0)+' of '+(run.total||'…'))+'</div>';
  if(R&&R.error)h+='<div class="fl-ref"><b>The last test stopped:</b> '+esc(R.error)+'</div>';
  if(!R||!R.factors){if(!run)h+='<div class="fl-ref">Nothing checked yet. The quick checks price one typical business per class with and without the filing, about a minute, and compare the result with what the filing says. No ISO calls.</div>';
    return h+flTestIso(f,R);}
  const fac=R.factors,pol=R.policy||[],ok1=R.ok&&R.ok.factors,nOk=fac.filter(x=>x.ok).length+pol.filter(x=>x.ok).length,nAll=fac.length+pol.length;
  h+='<div class="fl-ck">'+ic(ok1)+'<div><h4>The filed factors apply as written</h4><div class="mx-msg">Each row of the filing: the coverage\u2019s premium with the filing, against ISO\u2019s, must match the filed change (within '+R.tolerance.factor+'% over the risks it reaches). Single risks stray a little on small premiums because ISO rounds the rate.</div></div>'+
    '<span class="res">'+nOk+' of '+nAll+(ok1?' ✓':' ×')+'</span><div class="bd"><details class="fl-more"'+(ok1?'':' open')+'><summary>Show each row</summary><div class="fl-mdw"><table class="fl-md"><tr><th>Company</th><th>Coverage</th><th>Applies to</th><th class="r">Filed</th><th class="r">Our engine</th><th class="r">Per risk</th><th></th></tr>'+
    fac.map(x=>'<tr><td>'+co(x.company,x.state)+'</td><td>'+esc(x.coverage)+'</td><td>'+esc(x.appliesTo)+'<small>'+x.risks+' risk'+(x.risks===1?'':'s')+(FL.tech?' · '+esc(x.cite):'')+'</small></td><td class="r">'+flPct(x.filed)+'</td><td class="r"><b>'+flPct(x.got)+'</b></td><td class="r mx-msg">'+flPct(x.lo)+' to '+flPct(x.hi)+'</td><td>'+(x.ok?'✓':'×')+'</td></tr>').join('')+
    pol.map(x=>'<tr><td>'+co(x.company,x.state)+'</td><td colspan="2">'+esc(x.item)+'<small>every risk</small></td><td class="r">'+esc(x.filed)+'</td><td class="r" colspan="2">'+esc(x.got)+'</td><td>'+(x.ok?'✓':'×')+'</td></tr>').join('')+'</table></div></details>'+
    ((R.unreached||[]).length?'<div class="mx-msg">Not reached by the typical businesses: '+esc(R.unreached.join('; '))+'.</div>':'')+'</div></div>';
  const ok2=R.ok&&R.ok.effect,tol=R.tolerance.effect;
  h+='<div class="fl-ck">'+ic(ok2)+'<div><h4>The effect on premium is what we expect</h4><div class="mx-msg">'+(R.mode==='full'?'The whole typical set priced again':'The same risks priced again and set against the effect recorded for them, scaled to the whole typical set')+
    '. Expected starts as the effect recorded when the filing went into use; type your own to test against it.</div></div>'+
    '<span class="res">'+(ok2==null?'—':ok2?'Within \u00b1'+tol+' pt':'Outside \u00b1'+tol+' pt')+'</span><div class="bd"><div class="fl-mdw"><table class="fl-md"><tr><th>Company</th><th class="r">Expected</th><th class="r">Now</th><th class="r">Difference</th><th></th></tr>'+
    R.effects.map(e=>{const d=e.now!=null&&e.expected!=null?e.now-e.expected:null;return '<tr><td>'+co(e.company,e.state)+(e.movedCount?'<small>'+e.movedCount+' of '+e.matched+' risks priced differently from when it was recorded</small>':'')+(e.basis==='sample'?'<small>from the '+e.risks+' risks just priced (none recorded to compare)</small>':'')+'</td>'+
      '<td class="r"><input class="fl-ex" data-ex="'+esc(e.company+'|'+e.state)+'" value="'+(e.expected==null?'':flPct(e.expected).replace('\u2212','-'))+'" placeholder="none" aria-label="Expected effect for '+esc(flCoName(f,e.company))+'">'+
      (e.expectedFrom==='yours'?'<small><a href="#" data-exclear="'+esc(e.company+'|'+e.state)+'">use the recorded '+flPct(e.recorded)+'</a></small>':'<small>recorded</small>')+'</td>'+
      '<td class="r">'+flX(e.now)+'</td><td class="r">'+(d==null?'—':(d>=0?'+':'\u2212')+Math.abs(d).toFixed(1)+' pts')+'</td><td>'+(e.ok==null?'–':e.ok?'✓':'× outside \u00b1'+tol)+'</td></tr>';}).join('')+'</table></div>'+
    (R.effects.some(e=>e.movedCount)?'<details class="fl-more"><summary>Risks priced differently from when the effect was recorded</summary><table class="fl-md">'+R.effects.flatMap(e=>e.moved.map(m=>'<tr><td>'+esc(flShort(flCoName(f,e.company)))+'</td><td>'+esc(m.riskType+' · '+m.class+' · '+m.size+(m.construction?' · '+m.construction:''))+'</td><td class="r">'+esc(m.was)+' \u2192 <b>'+esc(m.now)+'</b></td></tr>')).join('')+'</table></details>':'')+
    (f.carrierExpected?'<div class="fl-ref"><b>'+esc(f.carrierExpected.what)+':</b> '+esc(f.carrierExpected.value)+' ('+esc(f.carrierExpected.parts)+').<div class="mx-msg">'+esc(f.carrierExpected.basis)+(FL.tech?' Source: '+esc(f.carrierExpected.cite||''):'')+'</div></div>':
      '<div class="mx-msg">This filing gives no expected figure of the insurer\u2019s own to compare with.</div>')+'</div></div>';
  return h+flTestIso(f,R)+flTry(f,R);}
function flTestIso(f,R){const P=FL.iso[f.serff],last=(R&&R.iso)||(P&&P.last);
  const ic=last&&last.ok!=null?(last.ok?'<span class="fl-ic">✓</span>':'<span class="fl-ic x">×</span>'):'<span class="fl-ic o">–</span>';
  const n=P?P.calls:null;
  let h='<div class="fl-ck">'+ic+'<div><h4>ISO agrees <span class="mx-msg" style="font:400 13.5px var(--font-body)">(optional spot check)</span></h4><div class="mx-msg">ISO only ever prices ISO\u2019s own rates, never an insurer\u2019s. One typical business per state is sent as its plain ISO request: ISO\u2019s price must equal our technical price. With the first check, the insurer\u2019s price is then ISO\u2019s times the filed factors.</div></div>'+
    '<span class="fl-cost iso">'+(n==null?'counting…':n?n+' ISO call'+(n===1?'':'s'):'free: already answered')+'</span><div class="bd">';
  if(last&&last.rows)h+='<div class="fl-mdw"><table class="fl-md"><tr><th>State</th><th>Business</th><th class="r">Our technical</th><th class="r">ISO</th><th></th></tr>'+last.rows.map(x=>'<tr><td>'+esc(x.state)+'</td><td>'+esc(x.riskType+' · '+x['class']+' · '+x.size+(x.construction?' · '+x.construction:''))+(x.detail?'<small>'+esc(x.detail)+'</small>':'')+'</td><td class="r">'+esc(x.ours||'—')+'</td><td class="r">'+esc(x.iso||'—')+'</td><td>'+(x.ok==null?'–':x.ok?'✓':'×')+(x.scenario?' <a href="#trace?scenario='+encodeURIComponent(x.scenario)+'">Trace</a>':'')+'</td></tr>').join('')+'</table></div><div class="mx-msg">Asked '+flDate(last.ranAt)+(last.sent?' · '+last.sent+' sent':' · ISO\u2019s stored answers, no call spent')+'.</div>';
  else h+='<div class="mx-msg">Not asked yet.</div>';
  if(FL.isoAsk===f.serff)h+='<div class="fl-ref">'+(n?'This sends '+n+' request'+(n===1?'':'s')+' to ISO from today\u2019s allowance.':'ISO has already answered '+(P&&P.requests.length===1?'this request':'these requests')+'; this reads its stored answer'+(P&&P.requests.length===1?'':'s')+' and spends nothing.')+
    '<div class="td-tools" style="margin-top:8px"><button class="btn primary" id="fl-isogo">'+(n?'Send '+n:'Compare')+'</button><button class="btn" data-iso="0">Cancel</button><span class="mx-msg" id="fl-isomsg"></span></div></div>';
  else h+='<div class="td-tools"><button class="btn" data-iso="1"'+(P?'':' disabled')+'>Ask ISO\u2026</button></div>';
  return h+'</div></div>';}
function flTry(f,R){const rs=(R&&R.risks)||[];if(!rs.length)return '';
  const k=FL.tryK!=null&&rs[FL.tryK]?FL.tryK:0,r=rs[k],t=Number(r.technical),c=Number(r.carrier),one=flStates(f).length===1;
  const lbl=x=>flShort(flCoName(f,x.company))+(one?'':' · '+x.state)+' · '+x.riskType+' · class '+x['class']+(x.construction?' · '+x.construction:'')+(R.mode==='full'?' · '+x.size:'');
  return '<div class="fl-ck"><span class="fl-ic o">?</span><div><h4>Try one</h4><div class="mx-msg">One of the typical businesses just priced, both ways.</div></div><span class="fl-cost">free</span>'+
    '<div class="bd"><select id="fl-try" aria-label="Business">'+rs.map((x,i)=>'<option value="'+i+'"'+(i===k?' selected':'')+'>'+esc(lbl(x))+'</option>').join('')+'</select>'+
    '<div class="fl-out">At ISO\u2019s rates <b>$'+t.toLocaleString()+'</b> · with the filing <b>$'+c.toLocaleString()+'</b> · '+flX(t?((c/t-1)*100).toFixed(1):null)+
    '<div class="mx-msg">'+esc(FL.tech?r.driver:String(r.driver||'').split(':')[0])+'</div></div>'+
    '<div class="td-tools"><a class="btn" href="#workbench">Price your own risk in the Workbench</a></div></div></div>';}
function flShortTab(f){const p=f.plain||{},h=flHead(f),lv=flLive(f),d=flDates(f);
  return (p.inShort?'<p class="fl-short">'+esc(p.inShort)+'</p>':'')+
    '<div class="fl-big">'+Object.keys(lv).map(c=>'<div class="'+(h[c]!=null?flHeat(h[c]):'')+'"><b>'+(h[c]!=null?flPct(h[c]):'—')+'</b><span>'+esc(flCoName(f,c))+': typical premium against ISO'+(lv[c].status!=='approved'?' (proposal)':'')+'</span></div>').join('')+
    (d.n?'<div><b>'+flDate(d.n).replace(/, \d+$/,'')+'</b><span>new policies'+(d.r?'; renewals from '+flDate(d.r):'')+'</span></div>':'')+'</div>'+
    (f.versions.some(v=>v.status==='draft')?'<div class="fl-ref">A proposal is pending: it is not in use until it is approved. Its effect is on the Effect on premium tab.</div>':'')+
    '<div class="mx-msg">The effect is estimated by pricing typical businesses both ways on our own engine. Changes always sit on top of ISO\u2019s rates in force on the policy date.</div>';}
function flSide(){const el=document.getElementById('fl-side'),f=flSel();let h='';
  if(f){const p=f.plain||{},hd=flHead(f),d=flDates(f);
    h+='<div class="cap2">Open filing</div><h3 style="margin:0;font:400 20px var(--font-heading)">'+esc((p.line||f.line)+' · '+(p.state||f.state))+'</h3>'+
      '<div class="mx-msg">'+Object.keys(flLive(f)).map(c=>esc(flShort(flCoName(f,c)))+' '+flPct(hd[c])).join(' · ')+(d.n?'<br>New policies from '+flDate(d.n)+(d.r?'; renewals from '+flDate(d.r):'')+'.':'')+'</div>'+
      '<div class="td-tools"><button class="btn primary" data-tab="test">Test it</button><a class="btn" href="#workbench">Price a risk</a></div>';}
  h+='<div class="cap2">Add a filing</div><div class="fl-drop" id="fl-drop" role="button" tabindex="0">Drop a filing packet (.zip) here<br><span class="mx-msg">or click to choose one. Nothing is put in use by an upload.</span></div>'+
    '<div class="cap2">How a filing gets here</div><ol class="fl-howto"><li>Reviewed in a Claude Code session, which writes our review and the proposals</li><li>Its packet uploaded here</li><li>The effect on premiums worked out</li><li>Put in use, tested against ISO and logged</li></ol>'+
    '<details class="fl-more"><summary>Words on this page</summary><dl class="fl-gl">'+FL_GLOSS.map(([k,v])=>'<dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd>').join('')+'</dl></details>';
  el.innerHTML=h;}
function flDraw(){const d=FL.d;if(!d)return;const fs=flFilings();
  if(!flSel()&&fs.length)FL.sel=flKey(fs[0]);
  flSumDraw();flBoard();flSide();
  const f=flSel(),el=document.getElementById('fl-entry');
  if(!f){el.hidden=true;el.innerHTML='';return;}el.hidden=false;
  const p=f.plain||{},steps=p.steps||FL_STEPS,at=steps.indexOf(p.step);
  const tabs=[['short','In short'],['rows','What changes'],['impact','Effect on premium'],['test','Test it'],['trail','Paper trail']];
  if(!tabs.some(([k])=>k===FL.tab))FL.tab='short';
  if(FL.tab==='test')flTestLoad(f);
  const body={short:()=>flShortTab(f),rows:()=>flRows(f),impact:()=>flImpact(f),test:()=>flTest(f),trail:()=>flTrail(f)}[FL.tab]();
  el.innerHTML='<div class="fl-fhead"><div><div class="mx-msg">'+esc(p.carrier||f.carrier)+(FL.tech?' · '+esc((f.id?f.id+' · ':'')+'SERFF '+f.serff+' · '+f.status+' · stage '+f.stage)+(f.proof?' · '+flProof(f):''):'')+'</div><h2>'+esc((p.line||f.line)+' · '+(p.state||f.state))+'</h2></div>'+
    '<div class="fl-steps">'+steps.map((s,i)=>'<span class="'+(i<at?'done':i===at?'now':'')+'">'+(i<at?'✓ ':'')+esc(s)+'</span>').join('')+'</div></div>'+
    '<div class="fl-tabs" role="tablist">'+tabs.map(([k,n])=>'<button role="tab" data-tab="'+k+'" aria-selected="'+(FL.tab===k)+'">'+n+'</button>').join('')+'</div>'+body;}
// ---- the test's data: one filing's result, the ISO plan, and the queue while anything runs
function flTestLoad(f){if(FL.t[f.serff]===undefined){FL.t[f.serff]=null;fetch('/api/console/filings/test?serff='+encodeURIComponent(f.serff)).then(r=>r.json()).then(j=>{FL.t[f.serff]=j.result;FL.st=j.status;if(FL.tab==='test')flDraw();flWatch();}).catch(()=>{});}
  if(FL.iso[f.serff]===undefined){FL.iso[f.serff]=null;fetch('/api/console/filings/iso?serff='+encodeURIComponent(f.serff)).then(r=>r.json()).then(j=>{FL.iso[f.serff]=j.error?null:j;if(FL.tab==='test')flDraw();}).catch(()=>{});}}
function flWatch(){const busy=FL.st&&(FL.st.running||(FL.st.waiting||[]).length);clearInterval(FL.poll);FL.poll=null;
  document.getElementById('fl-runall').disabled=!!busy;
  document.getElementById('fl-runmsg').textContent=busy?'Testing'+(FL.st.running?' '+(FL.st.running.done||0)+' of '+(FL.st.running.total||'…')+' risks':'')+((FL.st.waiting||[]).length?' · '+FL.st.waiting.length+' waiting':'')+'…':'On our engine. No ISO calls.';
  if(!busy)return;
  FL.poll=setInterval(()=>{if(document.getElementById('s-filings').hidden)return;fetch('/api/console/filings/test').then(r=>r.json()).then(j=>{const was=FL.st;FL.st=j.status;
    const doneNow=was&&was.running&&(!j.status.running||j.status.running.serff!==was.running.serff)?was.running.serff:null;
    if(doneNow)delete FL.t[doneNow];
    if(!j.status.running&&!(j.status.waiting||[]).length){flLoad();}else{flDraw();flWatch();}});},2000);}
function flUpShow(r){const el=document.getElementById('fl-up');if(!r){el.innerHTML='';return;}
  if(r.error){el.innerHTML='<div class="fl-card"><b>This file couldn\u2019t be read as a filing packet.</b><div class="mx-msg">'+esc(r.error)+'</div></div>';return;}
  const p=r.plain||{},j=r.impact,li=xs=>xs.map(x=>'<div class="mx-msg">'+esc(x)+'</div>').join('');
  el.innerHTML='<div class="fl-card"><b>'+esc(p.headline||'')+'</b>'+(p.saved?'<div class="mx-msg">'+esc(p.saved)+'</div>':'')+
    (p.problems&&p.problems.length?li(p.problems):'')+
    (j?'<div class="mx-msg" style="margin-top:4px">'+(j.state==='running'?'Working out the effect on premiums… '+j.done+' of '+j.total:'Effect on premiums worked out.')+
      (j.plain||[]).map(m=>'<br>'+esc(m)).join('')+'</div>':'')+
    '<details class="fl-more"><summary>Show what was saved</summary>'+li((r.written||[]).map(x=>'saved '+x))+li((r.skips||[]).map(x=>'already had '+x))+
      li((r.problems||[]))+(r.validation||[]).map(v=>'<div class="mx-msg">'+flChip(v.ok)+'checked '+esc(v.draft)+(v.ok?'':': '+esc(v.errors.join('; ')))+'</div>').join('')+'</details></div>';}
function flPoll(serff){fetch('/api/console/filings/jobs').then(r=>r.json()).then(d=>{const j=d.jobs.find(x=>x.serff===serff);if(!j||!FL.up)return;
  FL.up.impact=j;flUpShow(FL.up);if(j.state==='running')setTimeout(()=>flPoll(serff),3000);else flLoad();}).catch(()=>{});}
function flLoad(){Promise.all([fetch('/api/console/filings/board').then(r=>r.json()),fetch('/api/console/filings').then(r=>r.json()),fetch('/api/console/filings/test').then(r=>r.json())])
  .then(([b,d,t])=>{FL.b=b;FL.d=d;FL.st=t.status;FL.t={};FL.iso={};flCarriers();flDraw();flWatch();})
  .catch(e=>{document.getElementById('fl-board').innerHTML='<div class="mx-empty">Could not load the filings: '+esc(String(e))+'</div>';});}
function flPick(ev){const x=ev.target.closest('[data-f]');if(!x)return;FL.sel=x.dataset.f;FL.isoAsk=false;FL.tryK=null;flDraw();
  const e=document.getElementById('fl-entry');if(e.getBoundingClientRect().top>innerHeight*0.6)e.scrollIntoView({behavior:'smooth',block:'start'});}
document.getElementById('fl-board').addEventListener('click',flPick);
document.getElementById('fl-views').addEventListener('click',ev=>{const b=ev.target.closest('[data-v]');if(!b)return;FL.view=b.dataset.v;try{localStorage.setItem('fl-view',FL.view);}catch(e){}flBoard();});
function flSend(u,b){return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json());}
document.getElementById('s-filings').addEventListener('click',ev=>{const t=ev.target;
  const tb=t.closest('[data-tab]');if(tb){ev.preventDefault();FL.tab=tb.dataset.tab;flDraw();if(tb.closest('#fl-side'))document.getElementById('fl-entry').scrollIntoView({behavior:'smooth',block:'start'});return;}
  const rn=t.closest('[data-run]');if(rn){const fu=document.getElementById('fl-full');FL.full=!!(fu&&fu.checked);
    flSend('/api/console/filings/test',{serff:rn.dataset.run,full:FL.full}).then(j=>{FL.st=j.status;flDraw();flWatch();});return;}
  const is=t.closest('[data-iso]');if(is){FL.isoAsk=is.dataset.iso==='1'?(flSel()||{}).serff:false;flDraw();return;}
  if(t.id==='fl-isogo'){const f=flSel(),m=document.getElementById('fl-isomsg');t.disabled=true;m.textContent='Asking ISO…';
    flSend('/api/console/filings/iso',{serff:f.serff}).then(j=>{FL.isoAsk=false;if(FL.t[f.serff])FL.t[f.serff].iso=j;else FL.t[f.serff]={iso:j};delete FL.iso[f.serff];flDraw();}).catch(e=>{m.textContent=String(e);t.disabled=false;});return;}
  const xc=t.closest('[data-exclear]');if(xc){ev.preventDefault();const [c,s]=xc.dataset.exclear.split('|'),f=flSel();
    flSend('/api/console/filings/expected',{serff:f.serff,company:c,state:s,value:null}).then(j=>{FL.t[f.serff]=j.result;flDraw();});return;}
  if(t.closest('#fl-drop'))document.getElementById('fl-file').click();});
document.getElementById('s-filings').addEventListener('change',ev=>{const t=ev.target;
  if(t.id==='fl-full'){FL.full=t.checked;return;}
  if(t.id==='fl-try'){FL.tryK=+t.value;flDraw();return;}
  if(t.dataset.ex){const [c,s]=t.dataset.ex.split('|'),f=flSel(),v=parseFloat(t.value.replace('\u2212','-').replace(/[^\d.\-]/g,''));
    flSend('/api/console/filings/expected',{serff:f.serff,company:c,state:s,value:t.value.trim()===''||isNaN(v)?null:v}).then(j=>{if(j.result)FL.t[f.serff]=j.result;flDraw();});}});
document.getElementById('fl-runall').addEventListener('click',()=>flSend('/api/console/filings/test',{all:true}).then(j=>{FL.st=j.status;flDraw();flWatch();}));
document.getElementById('fl-tech').addEventListener('change',ev=>{FL.tech=ev.target.checked;flDraw();});
// the carrier picker: every carrier in the store; a remembered carrier that has gone falls back to all
function flCarriers(){const sel=document.getElementById('fl-carrier'),cs=(FL.b&&FL.b.carriers)||[];
  if(FL.carrier&&!cs.some(c=>c.code===FL.carrier))FL.carrier='';
  sel.innerHTML='<option value="">All carriers</option>'+cs.map(c=>'<option value="'+esc(c.code)+'">'+esc(c.name)+'</option>').join('');
  sel.value=FL.carrier;}
document.getElementById('fl-carrier').addEventListener('change',ev=>{FL.carrier=ev.target.value;FL.sel=null;
  try{localStorage.setItem('fl-carrier',FL.carrier);}catch(e){}flDraw();});
function flUpload(f){if(!f)return;const rd=new FileReader();
  document.getElementById('fl-up').innerHTML='<div class="fl-card mx-msg">Reading '+esc(f.name)+'…</div>';
  rd.onload=()=>{const data=String(rd.result).split(',')[1]||'';
    flSend('/api/console/filings/packet',{name:f.name,data}).then(r=>{FL.up=r;flUpShow(r);if(r.ok){FL.sel=r.serff;flLoad();if(r.impact)flPoll(r.serff);}})
      .catch(e=>flUpShow({error:String(e)}));};
  rd.readAsDataURL(f);}
document.getElementById('fl-file').addEventListener('change',ev=>{flUpload(ev.target.files[0]);ev.target.value='';});
document.getElementById('fl-side').addEventListener('dragover',ev=>{const d=ev.target.closest('#fl-drop');if(!d)return;ev.preventDefault();d.classList.add('over');});
document.getElementById('fl-side').addEventListener('dragleave',ev=>{const d=ev.target.closest('#fl-drop');if(d)d.classList.remove('over');});
document.getElementById('fl-side').addEventListener('drop',ev=>{const d=ev.target.closest('#fl-drop');if(!d)return;ev.preventDefault();d.classList.remove('over');flUpload(ev.dataTransfer.files[0]);});
document.getElementById('fl-side').addEventListener('keydown',ev=>{if(ev.target.id==='fl-drop'&&(ev.key==='Enter'||ev.key===' ')){ev.preventDefault();document.getElementById('fl-file').click();}});
addEventListener('hashchange',()=>{if((location.hash||'').startsWith('#filings'))flLoad();});
if((location.hash||'').startsWith('#filings'))flLoad();
"""


# ---- TC-27 / TC-29: the Test Plan Builder -----------------------------------------------------------------------------
# A line, states (no waves, D3) and per dimension the values to cover (from ISO's own domains, TC-26); a reduced grid,
# edges, an allowance that never drops a state (D20); live counters; Tier 0 at zero calls (TC-28); commit with a
# confirmation of what it will spend. Prefilled from the Readiness Matrix's gaps.

PLAN_HTML = """<section class="screen" id="s-plan" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Test Plan Builder</div><h1>Plan a round of checks</h1></div>
    <p>Describe one risk the way you would fill in a submission, mark the fields you want tried several ways, then
    apply it to as many states as you like. We build the smallest set of requests that covers it, reuse every answer
    ISO has already given, and show the cost before anything is sent.</p>
    <div class="bd-lines" id="pl-lines" role="group" aria-label="Line"><button data-l="GL">General Liability</button><button data-l="CP">Commercial Property</button></div></div>
  <div class="pl-shell">
    <nav class="pl-steps" id="pl-steps" aria-label="Steps"></nav>
    <div class="pl-screen">
      <section class="pl-step" data-step="0">
        <div><h2>How do you want to start?</h2><p class="mx-msg">All four lead to the same screens; they only change what is filled in for you.</p></div>
        <div class="pl-start" id="pl-start"></div>
        <div class="pl-presetrow" id="pl-presetrow" hidden><select id="pl-preset"><option value="">Choose a quick smoke, a QA tier or a layer…</option></select><span class="mx-msg" id="pl-presetmsg"></span></div>
        <div class="td-tools"><span class="mx-msg" id="pl-prefill"></span></div>
      </section>
      <section class="pl-step" data-step="1" hidden>
        <div><h2>Build the risk</h2><p class="mx-msg">Fill in one submission; anything left on Standard keeps the base risk. Switch on <b>Vary</b> for a field you want tried several ways.</p></div>
        <div class="bd-views" id="pl-tabs" role="tablist" aria-label="Screens"></div>
        <div id="pl-scrhd"></div>
        <div class="pl-form" id="pl-dims"></div>
        <div class="td-tools" id="pl-scrnav"></div>
      </section>
      <section class="pl-step" data-step="2" hidden>
        <div><h2>What to vary, and how</h2><p class="mx-msg">Everything else stays as the risk you built.</p></div>
        <div id="pl-varied"></div>
        <div class="td-tools"><select id="pl-addf" aria-label="Add a field to vary"></select></div>
        <h3>Method</h3>
        <div class="pl-method" id="pl-method"></div>
        <div class="td-tools"><label class="td-chk">Spend at most <input type="number" id="pl-allow" min="1" placeholder="no limit" style="width:110px"> calls (states are never dropped)</label></div>
        <div class="td-tools"><button class="btn primary" data-go="3">Next: choose states</button></div>
      </section>
      <section class="pl-step" data-step="3" hidden>
        <div><h2>Which states?</h2><p class="mx-msg">Click states on the map, or use a quick pick. "Not all" marks a state that does not offer a field you vary.</p></div>
        <div class="td-tools" id="pl-picks"></div>
        <div class="bd-map pl-map" id="pl-states"></div>
        <div class="td-tools"><span class="mx-msg" id="pl-stc"></span><button class="btn primary" data-go="4">Next: review</button></div>
      </section>
      <section class="pl-step" data-step="4" hidden>
        <div><h2>Review and commit</h2><p class="mx-msg">Nothing is sent until you commit. The free checks run on our engine only.</p></div>
        <div id="pl-review"></div>
        <div class="td-tools"><button class="btn" id="pl-t0">Run the free checks first</button><input id="pl-name" placeholder="Plan name" style="width:240px"><input id="pl-by" placeholder="Your name" style="width:180px">
          <label class="td-chk"><input type="checkbox" id="pl-startnow" checked> start sending now</label></div>
        <div id="pl-t0out"></div>
        <div class="td-tools"><button class="btn primary" id="pl-commit">Commit plan</button><span class="mx-msg" id="pl-msg"></span></div>
      </section>
    </div>
  </div>
</div><aside class="mx-side" id="pl-side" aria-live="polite"></aside></div></section>"""

BUILT["plan"] = PLAN_HTML

PLAN_CSS = """
#s-plan [hidden]{display:none!important}
.pl-shell{display:grid;grid-template-columns:210px minmax(0,1fr);gap:20px;align-items:start}
@media (max-width:1300px){.pl-shell{grid-template-columns:minmax(0,1fr)}.pl-steps{flex-direction:row;flex-wrap:wrap;position:static}}
.pl-steps{position:sticky;top:calc(var(--hdr,66px) + 12px);display:flex;flex-direction:column;gap:4px}
.pl-steps button{display:flex;gap:10px;align-items:center;text-align:left;border:0;background:none;padding:9px 12px;border-radius:var(--radius-md);font:500 14.5px var(--font-body);color:var(--color-neutral-700);cursor:pointer}
.pl-steps .n{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;background:var(--color-surface);font-size:12.5px;font-weight:600;flex:none}
.pl-steps button[aria-current="step"]{background:var(--color-card);color:var(--color-text);box-shadow:0 1px 3px color-mix(in srgb,#2d1d1a 8%,transparent)}
.pl-steps button[aria-current="step"] .n{background:var(--color-text);color:var(--color-bg)}
.pl-steps button.done .n{background:var(--teal);color:var(--color-text)}
.pl-steps small{display:block;font-weight:400;font-size:12.5px}
.pl-screen{background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-lg);padding:22px 24px;min-width:0}
.pl-step{display:flex;flex-direction:column;gap:16px}
.pl-step h2{margin:0;font:400 24px/1.2 var(--font-heading)}.pl-step h3{margin:0;font:500 17px var(--font-heading)}
.pl-step p.mx-msg{margin:6px 0 0}
.pl-start{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.pl-choice{border:1px solid var(--color-divider);border-radius:var(--radius-lg);padding:16px 18px;background:var(--color-bg);text-align:left;cursor:pointer;font:inherit;color:var(--color-text);display:flex;flex-direction:column;gap:6px}
.pl-choice:hover{background:var(--color-accent-100)}.pl-choice.on{border-color:var(--color-text);box-shadow:inset 0 0 0 1px var(--color-text);background:var(--color-card)}
.pl-choice b{font:500 18px var(--font-heading)}
.pl-presetrow{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
#pl-preset,#pl-addf{font:inherit;padding:8px 12px;border:1px solid var(--color-divider);background:var(--color-card);max-width:100%}
.bd-views button .c{font-size:11.5px;background:var(--teal);color:var(--color-text);border-radius:var(--radius-pill);padding:0 6px;margin-left:6px}
.pl-form{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px 18px}
.pl-f{display:flex;flex-direction:column;gap:6px;border:1px solid transparent;border-radius:var(--radius-md);padding:10px 12px;background:var(--color-bg);min-width:0}
.pl-f.vary{border-color:var(--teal-hover);background:var(--color-card)}
.pl-f .hd{display:flex;align-items:center;gap:8px}.pl-f .hd>span{font-weight:600;font-size:14px}
.pl-f .tog{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:13px;color:var(--color-neutral-700);cursor:pointer}
.pl-f .why{font-size:12.5px;color:var(--color-neutral-700)}.pl-f .gap{font-size:12px;color:var(--color-accent-700)}
.pl-f select,.pl-f input[type=text],.pl-f input[type=number],.pl-f input[list]{font:inherit;font-size:15px;color:var(--color-text);background:#fff;border:1px solid var(--color-divider);padding:8px 11px;width:100%;min-width:0}
.pl-vals{display:flex;flex-wrap:wrap;gap:5px}
.pl-v{font:inherit;font-size:13px;border:1px solid var(--color-divider);background:#fff;color:var(--color-text);border-radius:var(--radius-pill);padding:3px 10px;cursor:pointer}
.pl-v[aria-pressed="true"]{background:var(--teal-soft);border-color:var(--teal-hover);font-weight:600}
.pl-v.edge::after{content:" · edge";font-weight:400;color:var(--color-neutral-700);font-size:11.5px}
.pl-sw{appearance:none;width:34px;height:20px;border-radius:var(--radius-pill);background:var(--color-divider);position:relative;cursor:pointer;margin:0;flex:none}
.pl-sw::after{content:"";position:absolute;top:3px;left:3px;width:14px;height:14px;border-radius:50%;background:#fff;transition:left .15s}
.pl-sw:checked{background:var(--teal-hover)}.pl-sw:checked::after{left:17px}
@media (prefers-reduced-motion:reduce){.pl-sw::after{transition:none}}
.pl-vt{width:100%;border-collapse:collapse;font-size:14px}
.pl-vt th{text-align:left;font-weight:600;font-size:13px;color:var(--color-neutral-700);padding:6px 10px}
.pl-vt td{padding:10px;border-top:1px solid var(--color-divider);vertical-align:top}
.pl-method{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.pl-map .bd-tile{background:#fff;border:1px solid var(--color-divider)}
.pl-map .bd-tile[aria-pressed="true"]{background:var(--teal-soft);border-color:var(--teal-hover)}
.pl-map .bd-tile small{color:var(--color-accent-700);font-size:10.5px}
.pl-note{background:var(--color-accent-100);border:1px solid var(--color-accent-300);border-radius:var(--radius-md);padding:12px 14px;font-size:14px}
.pl-count{display:grid;grid-template-columns:1fr auto;gap:2px 10px;font-size:14px}
.pl-count b{font:600 16px var(--font-heading);text-align:right}
.pl-big{font:400 40px/1 var(--font-heading)}
.pl-chiplist{display:flex;flex-wrap:wrap;gap:5px}
.pl-chiplist span{font-size:12.5px;background:var(--color-card);border:1px solid var(--color-divider);border-radius:var(--radius-pill);padding:2px 9px}
"""

PLAN_JS = r"""
// ---- TC-27, reworked: risk first. One submission (fixed fields = the plan's base risk), the fields marked Vary (its
// dimensions), a method, then states. The counters and the commit are the server's (console.plans), unchanged.
const PL={line:'GL',step:0,mode:'risk',screen:null,base:{},vary:{},states:new Set(),cat:null,ctl:null,allStates:[],configs:[],presetName:'',
  method:'pairwise',timer:null,prev:null,presets:null};
const PL_SCREENS_GL=[['business','The business','What it does and how big it is',['class_code','premium_basis','exposure','subline']],
  ['locations','Locations','Where it operates',['locations','classifications','territory']],
  ['coverage','Coverage','Form and add-ons',['coverage_form','claims_made_year','retro_years','terrorism','exclusion_endorsement_premium']],
  ['limits','Limits and deductibles','How much, and what is retained',['occurrence_limit','general_aggregate','premops_bi_deductible','premops_pd_deductible','premops_bipd_deductible','prods_bi_deductible','prods_pd_deductible','prods_bipd_deductible']],
  ['plans','Rating plans','Experience, schedule, composite',['size_of_risk','experience_rating','erp_years','erp_annual_loss','schedule_rating','schedule_pct','schedule_extreme','package_mod','composite_rating','composite_basis','composite_exposure','composite_audited']],
  ['special','Dates and specialist settings','Edition, version, overrides',['effective_date','package_version','elp_override_premops','elp_override_prods','ilf_table_premops','ilf_table_prods']]];
const PL_DEPENDS={claims_made_year:['coverage_form','Claims Made'],retro_years:['coverage_form','Claims Made'],erp_years:['experience_rating','Yes'],erp_annual_loss:['experience_rating','Yes'],
  schedule_pct:['schedule_rating','Yes'],schedule_extreme:['schedule_rating','Yes'],composite_basis:['composite_rating','Yes'],composite_exposure:['composite_rating','Yes'],composite_audited:['composite_rating','Yes']};
const PL_COV_GL={'Prem/Ops':['Limits','Classification'],'Prod/CO':['Limits','Classification'],'Deductibles':['Deductibles'],'Cov B · P&AI':['Coverage form'],'Cov C · Med pay':['Coverage form']};
const PL_REG={Northeast:['ME','NH','VT','MA','RI','CT','NY','NJ','PA'],Midwest:['OH','MI','IN','IL','WI','MN','IA','MO','ND','SD','NE','KS'],
  South:['DE','MD','DC','VA','WV','NC','SC','GA','FL','KY','TN','AL','MS','AR','LA','OK','TX'],West:['MT','ID','WY','CO','NM','AZ','UT','NV','CA','OR','WA','AK','HI']};
const PL_STEPS=[['Start','How to begin'],['Build the risk','One submission'],['What to vary','Fields and method'],['States','Where to send it'],['Review','Cost and commit']];
function plDim(id){return (PL.cat||[]).find(d=>d.id===id);}
function plScreens(){if(PL.line==='GL'){const known=new Set(PL_SCREENS_GL.flatMap(x=>x[3])),rest=(PL.cat||[]).map(d=>d.id).filter(id=>!known.has(id));
    return PL_SCREENS_GL.map((x,i)=>i===PL_SCREENS_GL.length-1?[x[0],x[1],x[2],x[3].concat(rest)]:x);}
  const gs=[];(PL.cat||[]).forEach(d=>{let g=gs.find(x=>x[1]===d.group);if(!g){g=[d.group,d.group,'',[]];gs.push(g);}g[3].push(d.id);});return gs;}
function plRef(){return [...PL.states].sort()[0]||(PL.allStates.includes('OH')?'OH':PL.allStates[0])||'OH';}
function plLoad(){
  document.querySelectorAll('#pl-lines button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.l===PL.line));
  const ctl=PL.line==='GL'?fetch('/api/console/controls?lob=GL').then(r=>r.json()).then(c=>{PL.ctl=c.available?Object.fromEntries(c.controls.map(x=>[x.id,x])):null;if(PL.ctl)PL.ctl.__n=c.states.length;}).catch(()=>{PL.ctl=null;}):Promise.resolve(PL.ctl=null);
  return Promise.all([fetch('/api/console/catalog?lob='+PL.line).then(r=>r.json()).then(j=>{PL.allStates=j.states;}),ctl]).then(plCat);}
function plCat(){return fetch('/api/console/catalog?lob='+PL.line+'&state='+plRef()).then(r=>r.json()).then(j=>{PL.cat=j.dimensions;
  if(!PL.screen||!plScreens().some(x=>x[0]===PL.screen))PL.screen=plScreens()[0][0];plDraw();});}
// a value as the request wants it: numbers typed into a number field become numbers
function plNum(d,v){return d&&d.kind==='number'&&v!==''&&!isNaN(+v)?+v:v;}
function plSpec(){const a=parseInt(document.getElementById('pl-allow').value,10),base={};
  Object.entries(PL.base).forEach(([k,v])=>{if(v!==''&&v!=null&&!(k in PL.vary))base[k]=plNum(plDim(k),v);});
  const dims={};Object.entries(PL.vary).forEach(([k,v])=>{if(v.length)dims[k]=v.map(x=>plNum(plDim(k),x));});
  return {line:PL.line,states:[...PL.states].sort(),base,dims,configs:PL.configs||[],method:PL.method,reduced:false,edges:PL.method!=='all',allowance:isNaN(a)?null:a};}
function plShown(id){const dep=PL_DEPENDS[id];return PL.line!=='GL'||!dep||PL.base[dep[0]]===dep[1]||(PL.vary[dep[0]]||[]).includes(dep[1]);}
function plGap(id){const c=PL.ctl&&PL.ctl[id];if(!c)return '';const r=c.rated.length,dec=c.declined||[];
  return '<span class="gap">'+(r?'Rated in '+r+' of '+PL.ctl.__n+' states':'Never rated in any state yet')+(dec.length?' · not offered in '+esc(dec.join(', ')):'')+'</span>';}
function plLabel(d,v){return (d.labels||{})[v]||v;}
function plField(id){const d=plDim(id);if(!d||!plShown(id))return '';const vary=PL.vary[id],cur=PL.base[id]??'';
  const canVary=d.kind==='number'||d.values.length>1||d.perState;let input;
  if(d.perState)input='<div class="mx-msg">Each state has its own; the base risk uses each state’s standard. Vary it to try every state’s own extremes.</div>';
  else if(d.kind==='number')input='<input type="number" data-f="'+id+'" value="'+esc(cur)+'" placeholder="Standard" aria-label="'+esc(d.label)+'">';
  else if(d.values.length>80)input='<input list="pl-dl-'+id+'" data-f="'+id+'" value="'+esc(cur)+'" placeholder="Standard · type to search '+d.values.length+'" aria-label="'+esc(d.label)+'">'+
    '<datalist id="pl-dl-'+id+'">'+(d.suggested||[]).concat(d.values.filter(v=>!(d.suggested||[]).includes(v))).map(v=>'<option value="'+esc(v)+'">'+esc(plLabel(d,v))+'</option>').join('')+'</datalist>';
  else input='<select data-f="'+id+'" aria-label="'+esc(d.label)+'"><option value="">Standard</option>'+d.values.map(v=>'<option value="'+esc(v)+'"'+(v===cur?' selected':'')+'>'+esc(plLabel(d,v))+'</option>').join('')+'</select>';
  let vs='';
  if(vary&&d.perState)vs='<div class="mx-msg">Each state’s own first and last value.</div>';
  else if(vary&&d.kind==='number')vs='<input type="text" data-vn="'+id+'" value="'+esc(vary.join(', '))+'" placeholder="values to try, e.g. 0, 1, 5" aria-label="Values to try">';
  else if(vary){const sel=new Set(vary),pool=(d.suggested&&d.suggested.length?d.suggested:d.values.slice(0,24)),shown=pool.concat(vary.filter(v=>!pool.includes(v)));
    vs='<div class="pl-vals">'+shown.map(v=>'<button class="pl-v'+((d.edges||[]).includes(v)?' edge':'')+'" data-of="'+id+'" data-v="'+esc(v)+'" aria-pressed="'+sel.has(v)+'" title="'+esc(plLabel(d,v))+'">'+esc(d.suggested?v:plLabel(d,v))+'</button>').join('')+'</div>'+
      (d.values.length>pool.length?'<input list="pl-dl2-'+id+'" class="pl-addv" data-add="'+id+'" placeholder="Add another of the '+d.values.length+'" aria-label="Add a value"><datalist id="pl-dl2-'+id+'">'+d.values.map(v=>'<option value="'+esc(v)+'">'+esc(plLabel(d,v))+'</option>').join('')+'</datalist>':'');}
  return '<div class="pl-f'+(vary?' vary':'')+'"><div class="hd"><span>'+esc(d.label)+'</span>'+(canVary?'<label class="tog">Vary <input type="checkbox" class="pl-sw" data-vary="'+id+'"'+(vary?' checked':'')+'></label>':'')+'</div>'+input+vs+
    (d.exercises?'<span class="why">'+esc(d.exercises.charAt(0).toUpperCase()+d.exercises.slice(1))+'</span>':'')+plGap(id)+'</div>';}
function plStartDraw(){const ch=(id,t,dd)=>'<button class="pl-choice'+(PL.mode===id?' on':'')+'" data-mode="'+id+'"><b>'+t+'</b><span class="mx-msg">'+dd+'</span></button>';
  document.getElementById('pl-start').innerHTML=ch('risk','Build one risk','Fill in a submission, mark what to vary, then send it to many states. Best for a specific question.')+
    ch('gaps','Fill gaps','Fields never rated anywhere arrive marked to vary, and the states still to test are picked.')+
    ch('preset','From a preset','A quick smoke, a QA tier or a layer, then adjust it.')+
    ch('sweep','Sweep','Pick fields from one list and try every pair of their values (the earlier way).');
  document.getElementById('pl-presetrow').hidden=PL.mode!=='preset';}
function plRiskDraw(){const scs=plScreens(),sc=scs.find(x=>x[0]===PL.screen)||scs[0],i=scs.indexOf(sc),nv=x=>x[3].filter(id=>PL.vary[id]).length;
  document.getElementById('pl-tabs').innerHTML=scs.map(x=>'<button role="tab" data-scr="'+esc(x[0])+'" aria-selected="'+(x[0]===sc[0])+'">'+esc(x[1])+(nv(x)?'<span class="c">'+nv(x)+'</span>':'')+'</button>').join('');
  document.getElementById('pl-scrhd').innerHTML='<h3>'+esc(sc[1])+'</h3>'+(sc[2]?'<span class="mx-msg">'+esc(sc[2])+'</span>':'');
  document.getElementById('pl-dims').innerHTML=sc[3].map(plField).join('');
  document.getElementById('pl-scrnav').innerHTML=(i<scs.length-1?'<button class="btn" data-scr="'+esc(scs[i+1][0])+'">Next screen: '+esc(scs[i+1][1])+'</button>':'')+'<button class="btn primary" data-go="2">Next: what to vary</button>';}
function plVaryDraw(){const ks=Object.keys(PL.vary);
  document.getElementById('pl-varied').innerHTML=ks.length?'<table class="pl-vt"><tr><th>Field</th><th>Values to try</th><th>Coverage today</th><th></th></tr>'+ks.map(k=>{const d=plDim(k);if(!d)return '';
      return '<tr><td><b>'+esc(d.label)+'</b></td><td>'+(d.perState?'each state’s own extremes':esc(PL.vary[k].map(v=>plLabel(d,v)).join(' · ')||'none chosen yet'))+'</td><td>'+(plGap(k)||'<span class="mx-msg">—</span>')+'</td><td><button class="btn" data-unvary="'+k+'">Stop varying</button></td></tr>';}).join('')+'</table>':
    '<div class="pl-note">Nothing is varied yet, so each state gets the one risk you built'+(PL.configs.length?' plus the preset’s '+PL.configs.length+' scenario'+(PL.configs.length===1?'':'s'):'')+'. Add a field below, or carry on.</div>';
  document.getElementById('pl-addf').innerHTML='<option value="">Add a field to vary…</option>'+plScreens().map(x=>'<optgroup label="'+esc(x[1])+'">'+x[3].map(plDim).filter(d=>d&&!(d.id in PL.vary)&&(d.kind==='number'||d.values.length>1||d.perState)).map(d=>'<option value="'+d.id+'">'+esc(d.label)+'</option>').join('')+'</optgroup>').join('');
  const m=(id,t,dd)=>'<button class="pl-choice'+(PL.method===id?' on':'')+'" data-method="'+id+'"><b>'+t+'</b><span class="mx-msg">'+dd+'</span></button>';
  document.getElementById('pl-method').innerHTML=m('pairwise','Pairwise + edges','Every pair of values appears together once, plus each value at its extremes. The usual choice.')+
    m('edges','Edges only','Each varied field at its extremes, one at a time, beside the base risk. Cheapest.')+m('all','Every combination','Thorough but costly; the count is on the right.');}
function plVaryInit(d){return d.kind==='number'?[]:d.perState?[]:(d.edges||[]).length?d.edges.slice():d.values.slice(0,2);}
function plStatesDraw(){const dec=new Set(Object.keys(PL.vary).flatMap(k=>(PL.ctl&&PL.ctl[k]&&PL.ctl[k].declined)||[]));
  document.getElementById('pl-picks').innerHTML='<button class="btn" data-pick="all">All '+PL.allStates.length+'</button><button class="btn" data-pick="none">None</button>'+
    Object.keys(PL_REG).map(r=>'<button class="btn" data-pick="'+r+'">'+r+'</button>').join('')+'<button class="btn" data-pick="gaps">Still to test</button>'+(PL.ctl?'<button class="btn" data-pick="never">Never rated for what I vary</button>':'');
  document.getElementById('pl-states').innerHTML=BD_TILES.map(([s,y,x])=>{const ok=PL.allStates.includes(s);return '<button class="bd-tile'+(ok?'':' none')+'" data-tile="'+s+'"'+(ok?'':' disabled')+' aria-pressed="'+PL.states.has(s)+'" style="grid-row:'+(y+1)+';grid-column:'+(x+1)+'" title="'+esc(BOOT.names[s]||s)+'">'+s+(dec.has(s)?'<small>not all</small>':'')+'</button>';}).join('');
  document.getElementById('pl-stc').textContent=PL.states.size+' of '+PL.allStates.length+' states selected';}
function plReviewDraw(){const p=PL.prev,el=document.getElementById('pl-review');
  if(!PL.states.size){el.innerHTML='<div class="pl-note">Choose at least one state.</div>';return;}
  if(!p||p.error){el.innerHTML='<div class="mx-msg">'+esc(p&&p.error||'Counting…')+'</div>';return;}
  const bs=p.byState||{};
  el.innerHTML='<table class="pl-vt"><tr><th>State</th><th>Requests</th><th>Already answered</th><th>Not expressible</th><th>ISO calls</th></tr>'+Object.keys(bs).sort().map(s=>{const b=bs[s];
    return '<tr><td><b>'+s+'</b> <span class="mx-msg">'+esc(BOOT.names[s]||'')+'</span></td><td>'+b.scenarios+'</td><td>'+b.reused+'</td><td>'+(b.notApplicable||'—')+'</td><td><b>'+b.calls+'</b></td></tr>';}).join('')+'</table>'+
    ((p.notApplicableWhy||[]).length?'<details><summary class="mx-msg">Why some requests are not expressible</summary><table class="pl-vt">'+p.notApplicableWhy.map(x=>'<tr><td>'+x.state+'</td><td>'+esc(JSON.stringify(x.config))+'</td><td class="mx-msg">'+esc(x.detail)+'</td></tr>').join('')+'</table></details>':'');
  const c=document.getElementById('pl-commit');c.disabled=!p.scenarios;c.textContent='Commit plan · '+p.calls+' call'+(p.calls===1?'':'s');}
function plSide(){const p=PL.prev,el=document.getElementById('pl-side'),varied=Object.keys(PL.vary);
  let h='<div class="cap2">The plan so far</div>';
  if(!PL.states.size)h+='<div class="mx-msg">Choose states to see the cost.</div>';
  else if(!p)h+='<div class="mx-msg">Counting… (each request is built and checked against ISO’s stored answers)</div>';
  else if(p.error)h+='<div class="mx-msg">'+esc(p.error)+'</div>';
  else h+='<div><span class="pl-big">'+p.calls+'</span> ISO call'+(p.calls===1?'':'s')+'</div><div class="mx-msg">'+p.scenarios+' request'+(p.scenarios===1?'':'s')+' in '+p.statesKept+' of '+p.states+' state'+(p.states===1?'':'s')+' · about '+p.days+' day'+(p.days===1?'':'s')+' at 150 a day</div>'+
    '<div class="pl-count"><span>Base risk and pairwise</span><b>'+p.pairwise+'</b><span>Edge cases</span><b>'+p.edges+'</b>'+(p.presets?'<span>From the preset</span><b>'+p.presets+'</b>':'')+
    '<span>Already answered by ISO (reused, free)</span><b>'+p.alreadyAnswered+'</b><span>Not expressible in a state</span><b>'+p.notApplicable+'</b>'+(p.thinned?'<span>Left out by your call limit</span><b>'+p.thinned+'</b>':'')+
    '<span>Every combination (for scale)</span><b>'+p.cartesian.toLocaleString()+'</b><span>Calls left today</span><b>'+p.activeLeftToday+'</b></div>';
  const fixed=Object.entries(PL.base).filter(([k,v])=>v!==''&&v!=null&&!(k in PL.vary));
  h+='<div class="cap2">Fixed in the risk</div><div class="pl-chiplist">'+(fixed.length?fixed.map(([k,v])=>'<span>'+esc((plDim(k)||{}).label||k)+': '+esc(v)+'</span>').join(''):'<span>the standard base risk</span>')+'</div>'+
    '<div class="cap2">Varying</div><div class="pl-chiplist">'+(varied.length?varied.map(k=>'<span>'+esc((plDim(k)||{}).label||k)+(PL.vary[k].length?' · '+PL.vary[k].length:'')+'</span>').join(''):'<span>nothing</span>')+'</div>'+
    (PL.configs.length?'<div class="cap2">Preset</div><div class="mx-msg">'+esc(PL.presetName||'Prefilled')+': '+PL.configs.length+' scenario'+(PL.configs.length===1?'':'s')+' per state · <a href="#" id="pl-clearp">clear</a></div>':'')+
    '<div class="cap2">States</div><div class="pl-chiplist">'+([...PL.states].sort().map(s=>'<span>'+s+'</span>').join('')||'<span>none yet</span>')+'</div>';
  el.innerHTML=h;const c=document.getElementById('pl-clearp');if(c)c.onclick=e=>{e.preventDefault();PL.configs=[];PL.presetName='';plDraw();};}
function plPreview(){clearTimeout(PL.timer);PL.prev=null;plSide();if(!PL.states.size){if(PL.step===4)plReviewDraw();return;}
  PL.timer=setTimeout(()=>{const spec=plSpec();fetch('/api/console/plan/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spec})}).then(r=>r.json())
    .then(p=>{PL.prev=p;plSide();if(PL.step===4)plReviewDraw();}).catch(e=>{PL.prev={error:String(e)};plSide();});},350);}
function plDraw(){
  document.getElementById('pl-steps').innerHTML=PL_STEPS.map((x,i)=>'<button data-go="'+i+'"'+(i===PL.step?' aria-current="step"':'')+(i<PL.step?' class="done"':'')+'><span class="n">'+(i<PL.step?'✓':i+1)+'</span><span>'+x[0]+'<small>'+x[1]+'</small></span></button>').join('');
  document.querySelectorAll('#s-plan .pl-step').forEach(s=>s.hidden=+s.dataset.step!==PL.step);
  [plStartDraw,plRiskDraw,plVaryDraw,plStatesDraw,plReviewDraw][PL.step]();plPreview();}
function plGo(n){PL.step=n;plDraw();const s=document.querySelector('#s-plan .pl-screen');if(s&&s.getBoundingClientRect().top<0)s.scrollIntoView({block:'start'});}
function plReset(){PL.base={};PL.vary={};PL.configs=[];PL.presetName='';PL.screen=null;PL.prev=null;}
function plGaps(){PL.vary={};if(PL.ctl)(PL.cat||[]).filter(d=>PL.ctl[d.id]&&!PL.ctl[d.id].rated.length&&d.kind==='select'&&d.values.length>1&&d.id!=='premium_basis').slice(0,4).forEach(d=>PL.vary[d.id]=plVaryInit(d));
  else (PL.cat||[]).filter(d=>d.kind==='select'&&d.values.length>1).slice(0,3).forEach(d=>PL.vary[d.id]=plVaryInit(d));
  if(MX.data)PL.states=new Set((MX.data.stillToTest||[]).filter(g=>g.lob===PL.line).map(g=>g.state).filter(s=>PL.allStates.includes(s)));}
fetch('/api/console/presets').then(r=>r.json()).then(j=>{PL.presets=j.presets;document.getElementById('pl-preset').innerHTML='<option value="">Choose a quick smoke, a QA tier or a layer…</option>'+
  j.presets.map(p=>'<option value="'+p.id+'" title="'+esc(p.what)+'">'+esc(p.name)+' ('+(p.line==='GL'?'General Liability':'Property')+')</option>').join('');}).catch(()=>{});
document.getElementById('pl-preset').addEventListener('change',ev=>{const p=(PL.presets||[]).find(x=>x.id===ev.target.value);if(!p)return;
  plReset();PL.line=p.line;PL.configs=p.spec.configs||[];PL.presetName=p.name;PL.states=new Set(p.spec.states||[]);PL.mode='preset';
  document.getElementById('pl-presetmsg').textContent=p.what||'';plLoad().then(()=>plGo(2));});
document.getElementById('pl-lines').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b||b.dataset.l===PL.line)return;PL.line=b.dataset.l;plReset();PL.states=new Set();plLoad();});
document.getElementById('s-plan').addEventListener('click',ev=>{const t=ev.target;
  const g=t.closest('[data-go]');if(g){plGo(+g.dataset.go);return;}
  const m=t.closest('[data-mode]');if(m){PL.mode=m.dataset.mode;
    if(PL.mode==='gaps'){plGaps();plGo(2);}else if(PL.mode==='sweep')plGo(2);else if(PL.mode==='risk')plGo(1);else plStartDraw();return;}
  const sc=t.closest('[data-scr]');if(sc){PL.screen=sc.dataset.scr;plRiskDraw();return;}
  const v=t.closest('[data-of]');if(v){const k=v.dataset.of,a=PL.vary[k]||[],x=v.dataset.v;PL.vary[k]=a.includes(x)?a.filter(y=>y!==x):a.concat(x);plRiskDraw();plPreview();return;}
  const u=t.closest('[data-unvary]');if(u){delete PL.vary[u.dataset.unvary];plVaryDraw();plPreview();return;}
  const me=t.closest('[data-method]');if(me){PL.method=me.dataset.method;plVaryDraw();plPreview();return;}
  const tl=t.closest('#pl-states [data-tile]');if(tl&&!tl.disabled){const s=tl.dataset.tile;PL.states.has(s)?PL.states.delete(s):PL.states.add(s);plStatesDraw();plPreview();return;}
  const pk=t.closest('[data-pick]');if(pk){const k=pk.dataset.pick;
    if(k==='all')PL.states=new Set(PL.allStates);else if(k==='none')PL.states=new Set();
    else if(k==='gaps')PL.states=new Set(((MX.data&&MX.data.stillToTest)||[]).filter(x=>x.lob===PL.line).map(x=>x.state).filter(s=>PL.allStates.includes(s)));
    else if(k==='never'){const ks=Object.keys(PL.vary).filter(x=>PL.ctl&&PL.ctl[x]);PL.states=new Set(PL.allStates.filter(s=>ks.length&&ks.every(x=>!PL.ctl[x].rated.includes(s))));}
    else PL_REG[k].filter(s=>PL.allStates.includes(s)).forEach(s=>PL.states.add(s));
    plStatesDraw();plPreview();}});
document.getElementById('s-plan').addEventListener('change',ev=>{const t=ev.target;
  if(t.dataset.vary){const d=plDim(t.dataset.vary);if(t.checked)PL.vary[d.id]=plVaryInit(d);else delete PL.vary[d.id];plRiskDraw();plPreview();return;}
  if(t.dataset.f){const d=plDim(t.dataset.f);if(t.value&&d.kind!=='number'&&!d.values.includes(t.value)){t.value='';t.placeholder='Not one of ISO’s values here';return;}
    PL.base[t.dataset.f]=t.value;plRiskDraw();plPreview();return;}
  if(t.dataset.vn){PL.vary[t.dataset.vn]=t.value.split(',').map(x=>x.trim()).filter(Boolean);plPreview();return;}
  if(t.dataset.add){const d=plDim(t.dataset.add),v=t.value.trim();if(d.values.includes(v))PL.vary[d.id]=[...new Set((PL.vary[d.id]||[]).concat(v))];plRiskDraw();plPreview();return;}
  if(t.id==='pl-addf'&&t.value){const d=plDim(t.value);PL.vary[d.id]=plVaryInit(d);plVaryDraw();plPreview();return;}
  if(t.id==='pl-allow')plPreview();});
document.getElementById('pl-t0').onclick=()=>{const o=document.getElementById('pl-t0out');if(!PL.states.size)return;o.innerHTML='<div class="mx-msg">Rating the free checks on our engine…</div>';
  fetch('/api/console/plan/tier0',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({line:PL.line,states:[...PL.states].sort()})}).then(r=>r.json()).then(j=>{
    o.innerHTML='<div class="mx-need"><span class="chip '+(j.failed.length?'mismatch':'verified')+'">'+(j.failed.length?'×':'✓')+'</span><div><b>'+j.passed+' of '+j.checks+' free checks pass</b><div class="mx-msg">'+esc(j.note||'')+'</div></div></div>'+
      (j.failed.length?'<table class="pl-vt">'+j.failed.map(f=>'<tr><td>'+f.state+' · '+esc(f.check)+'</td><td>'+esc(f.detail)+'</td></tr>').join('')+'</table>':'');});};
document.getElementById('pl-commit').onclick=()=>{const m=document.getElementById('pl-msg'),p=PL.prev;if(!p||!p.scenarios){m.textContent='Nothing to commit yet.';return;}
  m.textContent='Rating each request on our engine and writing the plan…';
  fetch('/api/console/plan/commit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spec:plSpec(),name:document.getElementById('pl-name').value,
    by:document.getElementById('pl-by').value,start:document.getElementById('pl-startnow').checked})}).then(r=>r.json()).then(j=>{
    if(j.error){m.textContent=j.error;return;}location.hash='#queue?plan='+encodeURIComponent(j.id);}).catch(e=>{m.textContent=String(e);});};
let plStarted=false;
function plRoute(){const p=(location.hash||'').slice(1).split('?');if(p[0]!=='plan')return;const q=new URLSearchParams(p[1]||'');
  const sts=q.get('states')?q.get('states').split(','):null;
  if(q.get('lob'))PL.line=q.get('lob')==='GL'?'GL':'CP';
  if(sts&&q.get('config')){plReset();plStarted=true;PL.base=JSON.parse(q.get('config'));PL.states=new Set(sts);PL.mode='risk';
    document.getElementById('pl-prefill').textContent='From the Workbench: its risk, in '+sts.length+' state'+(sts.length===1?'':'s')+'.';plLoad().then(()=>plGo(1));}
  else if(sts){plReset();plStarted=true;const cov=(q.get('coverages')||'').split('|').filter(Boolean);PL.states=new Set(sts);PL.mode='gaps';
    document.getElementById('pl-prefill').textContent='From the Readiness Matrix: '+sts.length+' state'+(sts.length===1?'':'s')+', '+cov.length+' coverage'+(cov.length===1?'':'s')+'.';
    plLoad().then(()=>{(PL.cat||[]).forEach(d=>{const hit=PL.line==='CP'?cov.includes(d.coverage):cov.some(c=>(PL_COV_GL[c]||[]).includes(d.group));
      if(hit&&d.values.length>1&&d.id!=='class_code'&&d.id!=='effective_date')PL.vary[d.id]=plVaryInit(d);});plGo(2);});}
  else if(!plStarted){plStarted=true;plLoad();}}
addEventListener('hashchange',plRoute);plRoute();
"""

# ---- TC-31 / TC-32: the Queue & Run Log ------------------------------------------------------------------------------

QUEUE_HTML = """<section class="screen" id="s-queue" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Queue &amp; Run Log</div><h1>What's running, and what it found</h1></div>
    <p>ISO allows a set number of calls a day, shared out so planned work, refreshes and quick one-offs each get their
    turn. See what's waiting, pause or stop a plan and keep what it found, and read back every call we've made.</p></div>
  <div class="mx-stats" id="qu-lanes" style="grid-template-columns:repeat(4,minmax(0,1fr))"></div>
  <div id="qu-insp" hidden></div>
  <div class="cap2">Plans</div><div id="qu-plans"></div>
  <div class="cap2">Dispatch queue · next up</div><div id="qu-next"></div>
  <div class="cap2">Run log</div><div class="td-tools"><select id="qu-filter"><option value="">all plans</option></select></div><div id="qu-log"></div>
</div><aside class="mx-side" id="qu-side"></aside></div></section>"""

BUILT["queue"] = QUEUE_HTML

QUEUE_CSS = """
.qu-plan{border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:8px 10px;margin-bottom:6px;background:var(--color-bg);display:flex;flex-direction:column;gap:6px}
.qu-plan .hd{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.qu-plan .hd b{font:600 16px var(--font-heading)}
.qu-bar{display:flex;height:10px;border-radius:var(--radius-sm);overflow:hidden;background:var(--color-surface)}
.qu-bar i{display:block;height:100%}
.qu-st{font-size:12.5px;padding:1px 7px;border-radius:var(--radius-sm);border:1px solid var(--color-neutral-400)}
.qu-st.running{border-color:var(--color-accent);color:var(--color-accent-800);background:var(--color-accent-100)}
.qu-st.done{border-color:var(--color-accent-700);color:var(--color-accent-800)}
.qu-tbl{width:100%;border-collapse:collapse;font-size:13.5px}
.qu-tbl td{padding:9px 10px;border-top:1px solid var(--color-divider);vertical-align:top}
.qu-ev{font-size:12.5px;padding:1px 6px;border-radius:var(--radius-sm);border:1px solid var(--color-neutral-400);white-space:nowrap}
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
  <div class="mx-head"><div><div class="eyebrow">Regression Library</div><h1>The cases we trust</h1></div>
    <p>These are the requests we know the right answer to: ISO's own examples, our hand-checked golden cases, the app's
    samples and anything you've promoted. Re-run them any time to make sure today's engine still gets every one right.
    It's free.</p></div>
  <div class="mx-stats" id="lb-stats" style="grid-template-columns:repeat(5,minmax(0,1fr))"></div>
  <div class="td-tools"><button class="btn" id="lb-rerun">Re-run them all · free</button><span class="mx-msg" id="lb-prog"></span></div>
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
.lb-filters select,.lb-filters input{font:inherit;padding:8px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-md);background:var(--color-card)}
#lb-table th{font-size:13px;color:var(--color-neutral-700);text-align:left;padding:8px 10px;border-bottom:1px solid var(--color-text)}
.lb-r{font-size:12.5px;padding:2px 10px;border-radius:var(--radius-pill);border:1px solid var(--color-neutral-400);white-space:nowrap}
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
.iv .btn{padding:2px 8px;font-size:13.5px}
.iv .btn.iv-pass{border-color:var(--color-accent-700);color:var(--color-accent-800)}
.iv .btn.iv-fail{border-color:var(--ox);color:var(--ox-deep)}
.iv .btn.iv-exc{border-color:var(--color-neutral-500);color:var(--color-neutral-800)}
.iv-done{font-size:13.5px;white-space:nowrap}
.iv-done.pass{color:var(--color-accent-800)}.iv-done.fail{color:var(--ox-deep)}.iv-done.excuse{color:var(--color-neutral-700)}
.iv-done a{margin-left:6px}
.iv-form{display:flex;flex-direction:column;gap:6px;border:1px dashed var(--ox);border-radius:var(--radius-md);padding:8px;margin-top:6px;max-width:460px;background:var(--color-bg)}
.iv-form input,.iv-form select{font:inherit;padding:4px 6px}
.td-head .insp-slot{margin-left:auto}
.in-hd{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.in-hd b{font:600 18px var(--font-heading)}
.in-bar{display:flex;height:12px;border-radius:var(--radius-sm);overflow:hidden;background:var(--color-surface);max-width:420px;flex:1 1 220px}
.in-bar i{display:block;height:100%}
.in-flt .pl-chip{font-size:13.5px}
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
