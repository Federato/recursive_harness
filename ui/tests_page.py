"""The `/tests` page: set up a layered run, watch it, and keep the file.

Mounted through `ui.tester.dispatch`, which tries this module first. **The QA tab
is untouched.** It runs tiers, this runs layers, and they share the run store;
one launcher rewritten to do both would have meant editing the thing that
already works.

### What the page decides, and what it refuses to decide

* **The class is chosen basis-first.** ISO declares about 59 premium bases and
  about 1,190 class codes, and most bases are counts -- *Number of Zoos*, *Each
  Pier*, *Passenger Days* -- with no divisor at all. Picking the basis first
  narrows the class list and, more usefully, means the exposure box knows its
  own unit before anyone types in it.
* **The allowance never cuts states.** It thins the configuration list. Which
  configurations survived is written into the run file, because two runs of the
  same layer at different allowances are different matrices.
* **The budget is a ticker.** It shows what today has spent and stops nothing.
* **Pause holds; stop keeps what it found.** A stopped run is stored as a
  partial and names the states it never reached. Discarding two hundred calls'
  worth of answers because someone changed their mind about the last hundred is
  not a thing this page will do.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import layers                                                 # noqa: E402
import reviews                                                # noqa: E402
import runstore as store                                      # noqa: E402
import sweep                                                  # noqa: E402
import variants as V                                          # noqa: E402
from raas import NO_ISO                                       # noqa: E402

from . import charts, runfile                                 # noqa: E402

JOBS: dict = {}
JOBS_LOCK = threading.Lock()

#: A paused job checks this often. Short enough that resume feels immediate,
#: long enough that a held run is not a spin loop.
PAUSE_POLL = 0.25


# ------------------------------------------------------------------- the job

def _stop_check(job_id: str):
    """Return a callable sweep can ask between states.

    It blocks while the job is paused, which is how a pause is held without
    sweep knowing what a pause is.
    """
    def check():
        while True:
            with JOBS_LOCK:
                job = JOBS.get(job_id) or {}
                state = job.get("state")
            if state == "paused":
                time.sleep(PAUSE_POLL)
                continue
            return state == "stopping"
    return check


def _worker(job_id: str, args: dict) -> None:
    def progress(ev):
        with JOBS_LOCK:
            job = JOBS[job_id]
            job["event"] = ev
            if ev.get("phase") == "live" and "done" in ev:
                job["done"], job["total"] = ev["done"], ev["total"]
                row = ev.get("row")
                if row:
                    job["rows"].append(row)
            job["scenario"] = ev.get("scenario", job.get("scenario"))
            job["scenarios"] = ev.get("of", job.get("scenarios"))

    def scenario_done(result):
        with JOBS_LOCK:
            JOBS[job_id]["summaries"].append(result["summary"])

    try:
        out = layers.run(
            args["layer"], args.get("class_code", ""), args.get("exposure"),
            args.get("jurisdictions"), args.get("allowance"),
            bool(args.get("offline")), progress=progress,
            stop_check=_stop_check(job_id), label=args.get("label", ""),
            scenario_done=scenario_done)
    except Exception as exc:                                  # noqa: BLE001
        with JOBS_LOCK:
            JOBS[job_id].update(state="error", finished=True,
                                error=f"{type(exc).__name__}: {exc}")
        return

    # Read the change counts BEFORE the file is written, because writing adds
    # this run to the index and it would then be its own predecessor.
    try:
        changed = runfile.change_counts(out["plan"], out["results"])
    except Exception:                                         # noqa: BLE001
        changed = None

    try:
        path = runfile.write_run(out["plan"], out["results"],
                                 engine_version=_engine_version())
    except Exception as exc:                                  # noqa: BLE001
        path = None
        with JOBS_LOCK:
            JOBS[job_id]["file_error"] = f"{type(exc).__name__}: {exc}"

    bars_svg = charts.status_bars(
        _bars_summary(out["plan"]["rollup"], compared=not args.get("offline")))
    map_svg = charts.usa_map(layers.run_map(out["results"]),
                             title=out["plan"]["what"])

    with JOBS_LOCK:
        JOBS[job_id].update(
            state="done", finished=True, plan=out["plan"],
            rollup=out["plan"]["rollup"], changed=changed,
            file=str(path.name) if path else "",
            spent_today=store.spent_today(), bars=bars_svg, map=map_svg)


def _bars_summary(rollup: dict, compared: bool) -> dict:
    """A run's summed counts, in the list-of-placeholders shape `status_bars`
    reads -- it only ever calls `len()` on these, never touches an element."""
    return {
        "compared": compared, "rated": rollup["rated"], "agree": rollup["agree"],
        "differ": ["x"] * rollup["differ"],
        "premium_only": ["x"] * rollup["premium_only"],
        "engine_stopped": ["x"] * rollup["engine_stopped"],
        "not_applicable": ["x"] * rollup["not_applicable"],
        "errors": ["x"] * rollup["errors"],
    }


def _engine_version() -> str:
    try:
        return sweep.engine_version()
    except Exception:                                         # noqa: BLE001
        return ""


# --------------------------------------------------------------- the handlers

def _verdict_svg(a: dict) -> str:
    """One layer's all-time totals, as the verdict() chart reads them.

    `uncompared` is whatever `rated` doesn't already explain -- an offline
    scenario rates and is never compared, so it is neither an agreement nor a
    disagreement, and the chart has its own segment for exactly that.
    """
    uncompared = max(0, a["rated"] - a["agree"] - a["differ"]
                      - a["not_applicable"] - a["refused"])
    return charts.verdict(agree=a["agree"], differs=a["differ"],
                          not_applicable=a["not_applicable"],
                          refused=a["refused"], uncompared=uncompared)


def _spec() -> tuple:
    js = list(V.Declared.jurisdictions())
    agg = layers.stored_rollup()
    return 200, json.dumps({
        "layers": [{"id": k, **v, "configs": len(layers._configs(k))}
                   for k, v in sorted(layers.LAYERS.items())],
        "jurisdictions": js,
        # The page counts tests before anything is planned, so it needs to know
        # which jurisdictions rate without being compared. PR rates and is
        # never called: counting it as a live call would overstate every
        # estimate by one per configuration.
        "no_iso": sorted(NO_ISO & set(js)),
        "spent_today": store.spent_today(),
        "occurrence_points": list(layers.OCCURRENCE_POINTS),
        "aggregate_positions": list(layers.AGGREGATE_POSITIONS),
        "deductible_slots": [{"id": s, "label": V.BY_ID[s].label}
                             for s in layers.DEDUCTIBLE_SLOTS],
        "deductible_amount": layers.DEDUCTIBLE_AMOUNT,
        "runs": [{**e, "review_status": reviews.quick_status(e["file"])}
                 for e in runfile.entries()[-40:][::-1]],
        "aggregate": agg,
        "verdicts": {k: _verdict_svg(a) for k, a in agg.items()},
        "trend": charts.agreement_over_time(layers.stored_history()),
    }), "json"


def _classes(query) -> tuple:
    """Bases, and the classes declared for one of them, in one jurisdiction.

    Read from a single state deliberately. The declared class list is all but
    identical across states -- 1,187 of about 1,190 common to the six measured --
    so building the picker from all 51 would cost fifty corpus reads to change
    almost nothing on screen. The run itself still asks every state, which is
    where a genuine difference shows up as *not filed*.
    """
    juris = (query.get("juris") or "TX").upper()
    basis = query.get("basis") or ""
    try:
        d = sweep.declared(juris)
    except Exception as exc:                                  # noqa: BLE001
        return 400, json.dumps({"error": f"{type(exc).__name__}: {exc}"}), "json"
    bases = sorted(set(d.values(V.CLS, "PremOpsPremiumBasis")))
    out = {"juris": juris, "bases": bases, "basis": basis, "classes": []}
    if basis:
        codes = d.codes_for_basis(basis)
        out["classes"] = [{"code": c, "description": _desc(d, c)}
                          for c in codes]
    return 200, json.dumps(out), "json"


def _desc(d, code: str) -> str:
    try:
        return d.description(code)
    except Exception:                                         # noqa: BLE001
        return ""


def _plan(body) -> tuple:
    try:
        p = layers.plan(
            body.get("layer") or "L1", body.get("class_code") or "",
            body.get("exposure"), body.get("jurisdictions") or None,
            body.get("allowance"), offline=bool(body.get("offline")),
            size=body.get("size") or "full")
    except layers.PlanError as exc:
        return 400, json.dumps({"error": str(exc)}), "json"
    except Exception as exc:                                  # noqa: BLE001
        return 400, json.dumps(
            {"error": f"{type(exc).__name__}: {exc}"}), "json"
    # The scenario list can be long; the page needs its shape, not its bulk.
    p["scenarios"] = [{"describes": s["describes"], "basis": s["basis"],
                       "jurisdictions": len(s["jurisdictions"])}
                      for s in p["scenarios"]]
    return 200, json.dumps(p, default=str), "json"


def _start(body) -> tuple:
    layer = body.get("layer") or "L1"
    if layer not in layers.LAYERS:
        return 400, json.dumps({"error": f"unknown layer {layer!r}"}), "json"
    if layers.LAYERS[layer]["needs_class"] and not body.get("class_code"):
        return 400, json.dumps(
            {"error": f"{layer} needs a class code"}), "json"
    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {"id": job_id, "state": "running", "finished": False,
                        "started": time.time(), "rows": [], "summaries": [],
                        "done": 0, "total": 0, "scenario": 0, "scenarios": 0,
                        "layer": layer,
                        "class_code": body.get("class_code") or ""}
    threading.Thread(target=_worker, args=(job_id, body), daemon=True).start()
    return 200, json.dumps({"id": job_id}), "json"


def _state(job_id: str) -> tuple:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return 404, json.dumps({"error": "no such run"}), "json"
        out = {k: v for k, v in job.items() if k != "rows"}
        out["rows"] = list(job["rows"])[-60:]
        out["row_count"] = len(job["rows"])
    return 200, json.dumps(out, default=str), "json"


def _control(body) -> tuple:
    """Pause, resume or stop a running job."""
    job_id = body.get("id") or ""
    action = body.get("action") or ""
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return 404, json.dumps({"error": "no such run"}), "json"
        if job.get("finished"):
            return 400, json.dumps({"error": "that run has finished"}), "json"
        if action == "pause":
            job["state"] = "paused"
            job["paused_at"] = time.time()
        elif action == "resume":
            job["state"] = "running"
        elif action == "stop":
            job["state"] = "stopping"
        else:
            return 400, json.dumps(
                {"error": f"unknown action {action!r}"}), "json"
        return 200, json.dumps({"id": job_id, "state": job["state"]}), "json"


def dispatch(method: str, path: str, query: dict, body):
    """Handle a `/tests` route, or return None so the caller keeps looking.

    The review page is tried first, same reasoning as this module being tried
    first in `tester.dispatch` -- it is a separate concern with separate
    routes, sharing only the run file index.
    """
    from . import review_page
    out = review_page.dispatch(method, path, query, body)
    if out is not None:
        return out
    if path == "/tests" and method == "GET":
        return 200, PAGE, "html"
    if path.startswith("/runs/") and method == "GET":
        name = path.rsplit("/", 1)[-1] or "index.html"
        f = runfile.RUNS / name
        # Serve only from the runs directory, and only files it wrote.
        if ".." in name or "/" in name or not f.exists():
            return 404, json.dumps({"error": "no such run file"}), "json"
        return 200, f.read_text(encoding="utf-8"), "html"
    if not path.startswith("/api/tests"):
        return None
    if method == "GET":
        if path == "/api/tests/spec":
            return _spec()
        if path == "/api/tests/classes":
            return _classes(query)
        if path.startswith("/api/tests/run/"):
            return _state(path.rsplit("/", 1)[-1])
        return 404, json.dumps({"error": "not found"}), "json"
    if method == "POST":
        body = body or {}
        if path == "/api/tests/plan":
            return _plan(body)
        if path == "/api/tests/run":
            return _start(body)
        if path == "/api/tests/control":
            return _control(body)
        return 404, json.dumps({"error": "not found"}), "json"
    return None


PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>Layered tests -- GL rating engine</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--ink:#1a1d21;--muted:#6b7580;--line:#e3e8ee;--blue:#2b6cb0;
--red:#c0392b;--amber:#b7791f;--grey:#9aa5b1;--bg:#f7f9fb}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{background:#fff;border-bottom:1px solid var(--line);padding:12px 20px;
display:flex;align-items:baseline;gap:18px;flex-wrap:wrap}
header h1{font-size:16px;margin:0;font-weight:650}
header .sub{color:var(--muted);font-size:12.5px}
nav{margin-left:auto;display:flex;gap:6px;align-items:center}
nav a{font-size:13px;text-decoration:none;color:var(--blue);padding:5px 10px;
border:1px solid var(--line);border-radius:6px;background:#fff}
nav a.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.ticker{font-size:12.5px;color:var(--muted);padding:5px 10px;
border:1px solid var(--line);border-radius:6px;background:#fff}
.ticker b{color:var(--ink);font-variant-numeric:tabular-nums}
main{padding:16px 20px;display:grid;grid-template-columns:360px 1fr;gap:16px;
align-items:start}
@media(max-width:940px){main{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;
padding:13px 14px;margin-bottom:14px}
.card h2{font-size:12px;text-transform:uppercase;letter-spacing:.05em;
color:var(--muted);margin:0 0 9px;font-weight:650}
label{display:block;font-size:12px;color:var(--muted);margin:8px 0 2px}
select,input{width:100%;padding:6px 7px;border:1px solid #cbd2d9;
border-radius:5px;font-size:12.5px;background:#fff;color:var(--ink)}
select:disabled,input:disabled{background:#f0f3f6;color:var(--muted)}
button{background:var(--blue);color:#fff;border:0;border-radius:6px;
padding:8px 13px;font-size:13px;font-weight:600;cursor:pointer}
button.ghost{background:#fff;color:var(--ink);border:1px solid #cbd2d9;
font-weight:500}
button:disabled{opacity:.5;cursor:default}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}
.hint{font-size:11.5px;color:var(--muted);margin-top:5px}
.warn{font-size:11.5px;color:var(--amber);margin-top:5px}
.lay{border:1px solid var(--line);border-radius:6px;padding:7px 10px;margin:5px 0;
cursor:pointer;background:#fff;display:block}
.lay.on{border-color:var(--blue);box-shadow:0 0 0 1px var(--blue) inset}
.lay b{font-size:12.5px}
.lay span{display:block;font-size:11.5px;color:var(--muted)}
.gridwrap{border:1px solid var(--line);border-radius:6px;overflow:hidden}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;font-weight:650;color:var(--muted);font-size:11px;
text-transform:uppercase;letter-spacing:.04em;background:#f7f9fb;
border-bottom:1px solid var(--line);border-right:1px solid var(--line);
padding:7px 9px}
th:last-child,td:last-child{border-right:0}
td{padding:6px 9px;border-bottom:1px solid var(--line);
border-right:1px solid var(--line);vertical-align:top}
tr:last-child>td{border-bottom:0}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;
font-family:ui-monospace,"SF Mono",Consolas,monospace}
tr.total td{font-weight:650;background:#f7f9fb}
td.lbl{font-weight:650}
.st{font-weight:650;font-size:11.5px;white-space:nowrap}
.st.MATCH,.st.RATED{color:var(--blue)}
.st.DIFF{color:var(--red)}
.st.PREMIUM{color:var(--amber)}
.st.NOT,.st.BUILD{color:var(--grey)}
.det{color:var(--muted);font-size:11.5px}
#agg td.lbl{cursor:pointer}
#agg tr.hi{background:#eef4fb}
#agg tr.hi td.lbl{color:var(--blue)}
.dot{display:inline-block;width:9px;height:9px;border-radius:99px;margin-right:7px;
vertical-align:middle}
.dot.agree{background:var(--blue)}
.dot.differ{background:var(--red)}
.dot.partial{background:var(--amber)}
.dot.na{background:var(--grey)}
.vgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
@media(max-width:700px){.vgrid{grid-template-columns:1fr}}
.vcard{border:1px solid var(--line);border-radius:7px;padding:11px 13px}
.vcard h3{margin:0 0 5px;font-size:12.5px;font-weight:650}
.vcard h3 .dot{margin-right:6px}
.bar{height:7px;background:#eef2f6;border-radius:99px;overflow:hidden;margin:9px 0}
.bar>div{height:100%;background:var(--blue);width:0;transition:width .25s}
.note{font-size:11.5px;color:var(--muted);border-left:2px solid var(--line);
padding-left:8px;margin-top:6px}
.big{font-size:15px;font-weight:650;margin:2px 0 6px}
.scroll{max-height:520px;overflow:auto}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;
background:#eef2f6;color:var(--muted);margin-right:5px}
a.tag{text-decoration:none}
.tag.match{background:#eaf2fa;color:var(--blue)}
.tag.nomatch{background:#faf1e2;color:var(--amber)}
.err{color:var(--red);font-size:12px;margin-top:8px}
.pager{display:flex;gap:8px;align-items:center;justify-content:flex-end;margin-top:8px}
.pager button{padding:4px 10px;font-size:12px}
.pager span{font-size:11.5px;color:var(--muted)}
th.sortable{cursor:pointer;user-select:none}
th.sortable:hover{color:var(--ink)}
#histfilters select,#histfilters input{width:auto;display:inline-block}
.counter{border:1px solid var(--line);border-radius:6px;padding:9px 11px;
margin-bottom:4px;background:#fbfcfd}
.counter .n{font-size:20px;font-weight:650;font-variant-numeric:tabular-nums}
.counter .sum{font-size:12px;color:var(--muted);margin-top:2px}
.counter .cut{font-size:11.5px;color:var(--amber);margin-top:5px}
.counter .exact{font-size:11.5px;color:var(--blue);margin-top:5px}
.counts{display:flex;gap:20px;flex-wrap:wrap;margin:8px 0 2px}
.counts div{font-size:12px;color:var(--muted)}
.counts b{display:block;font-size:19px;color:var(--ink);
font-variant-numeric:tabular-nums;font-weight:650}
.counts b.bad{color:var(--red)}
.chg{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:9px}
.chg > div{border:1px solid var(--line);border-radius:7px;padding:9px 11px}
.chg .k{font-size:11px;color:var(--muted)}
.chg .v{font-size:23px;font-weight:650;font-variant-numeric:tabular-nums;
line-height:1.15}
.chg .w{font-size:11px;color:var(--muted);margin-top:2px}
.chg .v.bad{color:var(--red)} .chg .v.ok{color:#2f855a} .chg .v.new{color:var(--blue)}
#done h2{font-size:11px;text-transform:uppercase;letter-spacing:.05em;
color:var(--muted);margin:0 0 9px;font-weight:650}
a.opener{display:inline-block;background:var(--blue);color:#fff;
text-decoration:none;border-radius:6px;padding:8px 13px;font-size:13px;
font-weight:600}
</style></head><body>
<header>
  <h1>Layered tests</h1>
  <div class="sub">One kind of variation per layer &middot; every state, every run</div>
  <nav>
    <span class="ticker">Today: <b id="tick">--</b> live calls</span>
    <a href="/tests" class="on">Tests</a>
    <a href="/tester">Tester</a>
    <a href="/runs/index.html" target="_blank">Run files</a>
    <a href="/">Rate one</a>
  </nav>
</header>
<main>
<div>
  <div class="card">
    <h2>1 &middot; Layer</h2>
    <div id="layers"></div>
  </div>
  <div class="card" id="classcard">
    <h2>2 &middot; Class</h2>
    <label>Premium basis</label>
    <select id="basis"><option value="">-- pick a basis --</option></select>
    <div class="hint" id="basishint">Most bases are counts with no divisor at
      all, so the exposure only means something once a basis is chosen.</div>
    <label>Class code</label>
    <input id="filter" placeholder="type to filter" autocomplete="off">
    <select id="cls" size="7" disabled></select>
    <label>Exposure amount <span id="unit" class="det"></span></label>
    <input id="exposure" type="number" step="1" placeholder="1500000">
  </div>
  <div class="card">
    <h2>3 &middot; Allowance</h2>
    <div id="count" class="counter"></div>
    <label>Live ISO calls this run may spend</label>
    <input id="allowance" type="number" step="1" placeholder="leave blank for the full matrix">
    <div class="note">States are never cut to fit an allowance. The
      configuration list is thinned instead, and what was dropped is written
      into the run file.</div>
    <div class="row">
      <label style="margin:0"><input type="checkbox" id="offline"
        style="width:auto"> offline only (free)</label>
    </div>
    <div class="row">
      <button id="plan" class="ghost">Plan it</button>
      <button id="go">Run</button>
    </div>
    <div id="planout" class="hint"></div>
  </div>
</div>
<div>
  <div class="card" id="live" style="display:none">
    <h2>Running</h2>
    <div id="livehead" class="big"></div>
    <div class="bar"><div id="prog"></div></div>
    <div class="row">
      <button id="pause" class="ghost">Pause</button>
      <button id="stop" class="ghost">Stop and keep</button>
      <span class="det" id="livestate"></span>
    </div>
    <div class="note">A stopped run is stored as a partial and names the states
      it never reached. Nothing already answered is thrown away.</div>
    <div class="scroll gridwrap" style="margin-top:10px"><table id="rows"></table></div>
  </div>
  <div class="card" id="done" style="display:none">
    <h2>Result</h2>
    <div id="doneout"></div>
  </div>
  <div class="card">
    <h2>Aggregate</h2>
    <div class="gridwrap"><table id="agg"></table></div>
    <div class="note">Summed across every stored scenario for that layer, not
      just the page below. Click a layer, or use the Run files filter -- the
      two stay in sync.</div>
  </div>
  <div class="card">
    <h2>Verdict by layer &middot; all time</h2>
    <div class="vgrid" id="verdicts"></div>
  </div>
  <div class="card">
    <h2>Aggregate trend</h2>
    <div id="trend"></div>
    <div class="note">Every live-compared scenario across all four layers,
      oldest first.</div>
  </div>
  <div class="card">
    <h2>Run files</h2>
    <div class="row" id="histfilters" style="margin-top:0">
      <select id="histRunFilter" style="width:auto"><option value="">All runs</option></select>
      <input id="histClassFilter" placeholder="Filter by class" style="width:140px">
    </div>
    <div class="scroll gridwrap"><table id="hist"></table></div>
    <div class="pager" id="histpg"></div>
    <div class="note">Each run is a standalone file that opens without the app.
      They are not committed: a run holds ISO's licensed values.</div>
  </div>
</div>
</main>
<script>
const $ = s => document.querySelector(s);
let SPEC = null, LAYER = 'L1', CLASSES = [], JOB = null, TIMER = null;
const HIST_PAGE_SIZE = 10;
let histPage = 0;

async function get(u){ const r = await fetch(u); return r.json(); }
async function post(u,b){ const r = await fetch(u,{method:'POST',
  headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)});
  return r.json(); }

function needsClass(){ return (SPEC.layers.find(l=>l.id===LAYER)||{}).needs_class; }

function drawLayers(){
  $('#layers').innerHTML = SPEC.layers.map(l =>
    `<div class="lay${l.id===LAYER?' on':''}" data-id="${l.id}">
       <b>${l.id} &middot; ${l.name}</b><span>${l.what}</span></div>`).join('');
  document.querySelectorAll('.lay').forEach(el => el.onclick = () => {
    LAYER = el.dataset.id; drawLayers(); syncClassCard(); drawCount(); });
}

function syncClassCard(){
  const need = needsClass();
  $('#classcard').style.opacity = need ? 1 : .72;
  $('#basishint').textContent = need
    ? 'Most bases are counts with no divisor at all, so the exposure only means something once a basis is chosen.'
    : 'Optional for this layer. Leave it alone to test the base submission\'s own class.';
}

async function loadBases(){
  const d = await get('/api/tests/classes');
  $('#basis').innerHTML = '<option value="">-- pick a basis --</option>' +
    d.bases.map(b=>`<option>${b}</option>`).join('');
}

async function loadClasses(){
  const b = $('#basis').value;
  $('#unit').textContent = b ? '(' + b + ')' : '';
  if(!b){ CLASSES=[]; $('#cls').innerHTML=''; $('#cls').disabled=true; return; }
  $('#cls').disabled = true; $('#cls').innerHTML = '<option>reading ISO\'s table...</option>';
  const d = await get('/api/tests/classes?basis=' + encodeURIComponent(b));
  CLASSES = d.classes; $('#cls').disabled = false; drawClasses();
}

function drawClasses(){
  const q = ($('#filter').value||'').toLowerCase();
  const hit = CLASSES.filter(c => !q || c.code.includes(q) ||
    (c.description||'').toLowerCase().includes(q));
  $('#cls').innerHTML = hit.slice(0,400).map(c =>
    `<option value="${c.code}">${c.code} &nbsp; ${c.description}</option>`).join('');
  $('#basishint').textContent = `${hit.length} of ${CLASSES.length} classes`;
}

// The count, from the spec alone -- no server call, so it moves as you type.
// It assumes the class is filed in every jurisdiction, which is true of all but
// a handful; `Plan it` reads the declaration for real and replaces this with
// the exact figure. Saying "about" until then is the honest version.
function estimate(){
  const spec = (SPEC.layers.find(l => l.id === LAYER) || {});
  const configs = spec.configs || 1;
  const states = (SPEC.jurisdictions || []).length;
  const noIso = (SPEC.no_iso || []).length;
  const offline = $('#offline').checked;
  const perConfigLive = offline ? 0 : Math.max(0, states - noIso);
  const allowance = parseInt($('#allowance').value) || null;
  let kept = configs;
  if (allowance && perConfigLive && configs * perConfigLive > allowance)
    kept = Math.max(1, Math.floor(allowance / perConfigLive));
  return {configs, kept, states, offline, perConfigLive,
          tests: kept * states, live: kept * perConfigLive, allowance};
}

function drawCount(exact){
  const e = estimate();
  const t = exact ? exact.tests : e.tests;
  const live = exact ? exact.live : e.live;
  const about = exact ? '' : 'about ';
  let h = `<div class="n">${t.toLocaleString()} tests</div>`
        + `<div class="sum">${e.kept} configuration${e.kept === 1 ? '' : 's'}`
        + ` &times; ${e.states} jurisdictions`
        + (e.offline ? ' &middot; offline, no ISO calls'
                     : ` &middot; ${about}${live.toLocaleString()} against ISO`)
        + '</div>';
  if (e.kept < e.configs)
    h += `<div class="cut">Thinned to fit ${e.allowance} calls: `
       + `${e.kept} of ${e.configs} configurations. Every jurisdiction kept.</div>`;
  if (!e.offline && !e.allowance && live > 60)
    h += `<div class="cut">More than a day's usual 60 calls, and no allowance `
       + `set. The ticker reports; it does not stop you.</div>`;
  if (exact) h += `<div class="exact">Counted from ISO's declaration, `
                + `not estimated.</div>`;
  $('#count').innerHTML = h;
}

function body(){
  const b = {layer: LAYER};
  if($('#cls').value) b.class_code = $('#cls').value;
  if($('#exposure').value) b.exposure = parseFloat($('#exposure').value);
  if($('#allowance').value) b.allowance = parseInt($('#allowance').value);
  b.offline = $('#offline').checked;
  return b;
}

$('#plan').onclick = async () => {
  $('#planout').textContent = 'planning...';
  const p = await post('/api/tests/plan', body());
  if(p.error){ $('#planout').innerHTML = '<span class="err">'+p.error+'</span>'; return; }
  let s = `<b>${p.cost.scenarios}</b> scenario(s), <b>${p.cost.ratings}</b> engine ratings, `
        + `<b>${p.cost.live_calls}</b> ISO calls.`;
  (p.groups||[]).forEach(g => { if(g.basis)
    s += `<br>basis <b>${g.basis}</b> in ${g.jurisdictions.length} jurisdictions.`; });
  if(p.undeclared && p.undeclared.length)
    s += `<br><span class="warn">Not filed in ${p.undeclared.length}: `
       + p.undeclared.join(' ') + ' -- reported, not dropped.</span>';
  if(p.thinning && p.thinning.applied)
    s += `<br><span class="warn">Thinned to fit ${p.thinning.allowance} calls: `
       + `${p.thinning.configs_kept} of ${p.thinning.configs_planned} configs, `
       + `all ${p.jurisdictions.length} jurisdictions kept.</span>`;
  $('#planout').innerHTML = s;
  // The plan read the declaration in every state, so it knows what the
  // estimate could only assume -- including a class ISO does not file
  // somewhere, which makes the real count smaller.
  drawCount({tests: p.cost.ratings, live: p.cost.live_calls});
};

$('#go').onclick = async () => {
  const r = await post('/api/tests/run', body());
  if(r.error){ $('#planout').innerHTML = '<span class="err">'+r.error+'</span>'; return; }
  JOB = r.id; $('#live').style.display=''; $('#done').style.display='none';
  $('#go').disabled = true; poll();
};

$('#pause').onclick = async () => {
  const st = $('#pause').textContent === 'Pause' ? 'pause' : 'resume';
  await post('/api/tests/control', {id: JOB, action: st});
};
$('#stop').onclick = async () => {
  await post('/api/tests/control', {id: JOB, action: 'stop'});
  $('#stop').disabled = true; $('#livestate').textContent = 'stopping after this state...';
};

function poll(){
  clearTimeout(TIMER);
  TIMER = setTimeout(async () => {
    const s = await get('/api/tests/run/' + JOB);
    render(s);
    if(!s.finished) poll(); else finish(s);
  }, 700);
}

function render(s){
  $('#pause').textContent = s.state === 'paused' ? 'Resume' : 'Pause';
  $('#livestate').textContent = s.state;
  const ev = s.event || {};
  $('#livehead').textContent = (ev.describes || '') +
    (s.scenarios ? `  (scenario ${s.scenario} of ${s.scenarios})` : '');
  const pct = s.total ? Math.round(100*s.done/s.total) : 0;
  $('#prog').style.width = pct + '%';
  $('#rows').innerHTML =
    '<tr><th>State<th>Status<th class=n>Ours<th class=n>ISO<th class=n>Diff</tr>' +
    (s.rows||[]).slice().reverse().map(r => {
      const c = (r.status||'').split(' ')[0];
      return `<tr><td><b>${r.juris}</b><td class="st ${c}">${r.status||''}`
           + `<td class=n>${r.ours||'--'}<td class=n>${r.iso||'--'}`
           + `<td class=n>${r.delta||''}</tr>`;
    }).join('');
}

function finish(s){
  $('#go').disabled = false; $('#stop').disabled = false;
  $('#live').style.display='none'; $('#done').style.display='';
  if(s.error){ $('#doneout').innerHTML = '<span class="err">'+s.error+'</span>'; return; }
  const r = s.rollup||{}, p = s.plan||{};
  const differ = (r.differ||0) + (r.premium_only||0);
  let h = p.offline
    ? `<div class="big">${r.rated||0} rated &middot; ${r.not_applicable||0} `
      + `not applicable &middot; ${r.engine_stopped||0} refused</div>`
      + `<div class="note">Engine only &mdash; no ISO comparison, 0 live calls. `
      + `Nothing here says whether a premium is right.</div>`
    : `<div class="big">${r.agree||0} agree &middot; ${differ} differ `
      + `&middot; ${r.not_applicable||0} not applicable</div>`;
  h += `<div class="counts">`
     + `<div><b>${r.scenarios||0}</b>scenarios</div>`
     + `<div><b>${r.rated||0}</b>rated</div>`
     + (p.offline ? '' : `<div><b>${r.agree||0}</b>agree</div>`
        + `<div><b class="${differ?'bad':''}">${differ}</b>differ</div>`)
     + `<div><b>${r.live_calls||0}</b>ISO calls</div></div>`;
  if(s.bars) h += `<div style="margin-top:12px">${s.bars}</div>`;
  if(s.map) h += `<div style="margin-top:10px">${s.map}</div>`;
  // The same counts the run file carries, from the same computation.
  const c = s.changed;
  if(c){
    const box = (k,v,cls,w) => `<div><div class="k">${k}</div>`
      + `<div class="v ${cls}">${v}</div><div class="w">${w||'none'}</div></div>`;
    const cov = c.newly_covered.length ? '+'+c.newly_covered.length
      : (c.new_configs.length ? c.new_configs.length+' new configs' : '0');
    h += `<h2 style="margin-top:14px">What changed since `
       + `${(c.at||'').slice(0,10)}</h2><div class="chg">`
       + (c.mode === 'offline'
          ? box('Newly refusing', c.newly_refusing.length, 'bad', c.newly_refusing.slice(0,4).join(', '))
            + box('No longer refusing', c.no_longer_refusing.length, 'ok', c.no_longer_refusing.slice(0,4).join(', '))
            + box('Premium changed', c.premium_changed.length, c.premium_changed.length?'bad':'', c.premium_changed.slice(0,4).join(', '))
          : box('New problems', c.new_problems.length, 'bad', c.new_problems.slice(0,4).join(', '))
            + box('No longer failing', c.no_longer_failing.length, 'ok', c.no_longer_failing.slice(0,4).join(', '))
            + box('Still failing', c.still_failing.length, '', c.still_failing.slice(0,4).join(', ')))
       + box('Newly covered', cov, 'new', c.newly_covered.slice(0,4).join(', '))
       + `</div><div class="note">Against ${c.against}. `
       + (c.mode === 'offline'
          ? 'A premium that moved when no rule changed is a regression.'
          : '<b>No longer failing is not the same as fixed</b> — a state can stop '
            + 'failing because the configuration that broke it was not repeated.')
       + `</div>`;
  } else {
    h += `<div class="note">First recorded run of this layer and class, so `
       + `there is nothing to compare it with.</div>`;
  }
  if(p.undeclared && p.undeclared.length)
    h += `<div class="note">Class not filed in ${p.undeclared.length} `
       + `jurisdictions: ${p.undeclared.join(' ')}</div>`;
  if(p.stopped_after !== undefined && p.stopped_after !== null)
    h += `<div class="warn">Partial run: stopped after ${p.stopped_after} scenario(s).</div>`;
  if(s.file) h += `<div class="row"><a class="opener" href="/runs/${s.file}" `
    + `target="_blank">Open the run file &rarr;</a></div>`
    + `<div class="note">The matrix, the ${p.layer === 'L3' ? 'response curve'
        : p.layer === 'L4' ? 'per-slot movement' : 'spread across states'} and `
    + `every state are in the file.</div>`;
  if(s.file_error) h += `<div class="err">the run ran; the file did not write: ${s.file_error}</div>`;
  $('#doneout').innerHTML = h;
  refresh();
}

let histSort = { key: 'when', dir: 'desc' };

// One field to sort or filter by per column. `run` sorts and filters on the
// same label the cell shows -- "L1 Smoke" -- so what you pick in the dropdown
// is exactly what you'd click a header to reach.
const HIST_FIELD = {
  when: e => e.at || '',
  run: e => `${e.layer} ${e.name}`,
  class: e => e.class_code || '',
};

function histCompare(key, dir){
  const get = HIST_FIELD[key], sign = dir === 'asc' ? 1 : -1;
  return (a, b) => {
    let av = get(a), bv = get(b);
    if(key === 'class'){                    // "13352" before "9001" needs a
      const an = parseFloat(av), bn = parseFloat(bv);  // numeric compare, not
      if(!isNaN(an) && !isNaN(bn)){ av = an; bv = bn; } // a string one
    }
    if(av < bv) return -sign;
    if(av > bv) return sign;
    return 0;
  };
}

function histFiltered(){
  const runF = $('#histRunFilter') ? $('#histRunFilter').value : '';
  const clsF = $('#histClassFilter')
    ? $('#histClassFilter').value.trim().toLowerCase() : '';
  return (SPEC.runs || []).filter(e =>
    (!runF || `${e.layer} ${e.name}` === runF)
    && (!clsF || String(e.class_code || '').toLowerCase().includes(clsF)));
}

function populateHistFilters(){
  // Options come from the four known layers, not from which ones happen to
  // have a rendered run file yet -- the aggregate can hold scenarios for a
  // layer (via the API, or the CLI) before its first run file ever exists,
  // and picking that layer here must not silently fail to select.
  const sel = $('#histRunFilter'), had = sel.value;
  const opts = ['<option value="">All runs</option>'].concat(
    (SPEC.layers || []).map(l => `<option>${l.id} ${l.name}</option>`));
  sel.innerHTML = opts.join('');
  sel.value = had;                    // keep the choice across a refresh
  sel.onchange = () => { histPage = 0; drawHist(); drawAgg(); };
  $('#histClassFilter').oninput = () => { histPage = 0; drawHist(); };
}

function aggDot(r){
  // Same accounting as the verdict card below it: whatever `rated` doesn't
  // explain as agree/differ/N-A/refused is uncompared -- an offline scenario,
  // most often -- and it must not read as a silent agree.
  if(!r.rated) return 'na';                 // nothing stored for this layer yet
  const uncompared = Math.max(0, r.rated - r.agree - r.differ - r.na - r.refused);
  if(r.differ || r.refused) return 'differ';
  if(r.agree === 0) return 'na';
  if(r.na || uncompared) return 'partial';
  return 'agree';
}

function dotSpan(kind){ return `<span class="dot ${kind}"></span>`; }

function histDot(e){
  // A run file doesn't carry a not_applicable count, so this reads what it
  // does have: offline means nothing was compared at all, a differ count or
  // any refused state means red, everything rated agreeing means blue, and
  // the remainder (live, no differ, not fully agreeing) is not-applicable
  // rows softening an otherwise clean run.
  if(e.offline) return 'na';
  if((e.differ||0) || (e.refusing||[]).length) return 'differ';
  if(e.rated && (e.agree||0) >= e.rated) return 'agree';
  return 'partial';
}

function reviewTag(e){
  // Independent of the outcome dot -- a run can disagree AND already have a
  // posted explanation, or agree cleanly and never need a review record at
  // all, which is why "no tag" is a normal, common state here. Never claims
  // "fully reviewed" from this cheap a check -- see quick_status's docstring.
  if(e.review_status === 'has_notes')
    return `<a class="tag match" href="/review/${e.file}">has notes</a>`;
  if(e.review_status === 'pending')
    return `<a class="tag nomatch" href="/review/${e.file}">review started</a>`;
  return '';
}

function drawAgg(){
  const agg = SPEC.aggregate || {}, current = $('#histRunFilter').value;
  const rows = (SPEC.layers || []).map(l => {
    const label = `${l.id} ${l.name}`, a = agg[l.id] || {};
    return { label, id: l.id,
      scenarios: a.scenarios||0, rated: a.rated||0, agree: a.agree||0,
      differ: a.differ||0, na: a.not_applicable||0, refused: a.refused||0 };
  });
  const total = rows.reduce((t, r) => {
    ['scenarios','rated','agree','differ','na','refused'].forEach(
      k => t[k] = (t[k]||0) + r[k]);
    return t;
  }, {});

  $('#agg').innerHTML =
    '<tr><th>Layer<th class=n>Scenarios<th class=n>Rated<th class=n>Agree'
    + '<th class=n>Differ<th class=n>N/A<th class=n>Refused</tr>'
    + rows.map(r =>
        `<tr class="${r.label===current?'hi':''}"><td class=lbl>`
        + `${dotSpan(aggDot(r))}${r.label}`
        + `<td class=n>${r.scenarios}<td class=n>${r.rated}<td class=n>${r.agree}`
        + `<td class=n>${r.differ}<td class=n>${r.na}<td class=n>${r.refused}</tr>`)
        .join('')
    + `<tr class="total"><td class=lbl>All layers<td class=n>${total.scenarios||0}`
    + `<td class=n>${total.rated||0}<td class=n>${total.agree||0}`
    + `<td class=n>${total.differ||0}<td class=n>${total.na||0}`
    + `<td class=n>${total.refused||0}</tr>`;

  document.querySelectorAll('#agg td.lbl').forEach(td => {
    if(td.parentElement.classList.contains('total')) return;
    td.onclick = () => {
      const label = td.textContent;      // the dot span carries no text
      const sel = $('#histRunFilter');
      sel.value = sel.value === label ? '' : label;
      histPage = 0; drawHist(); drawAgg();
    };
  });
}

function drawVerdicts(){
  const verdicts = SPEC.verdicts || {}, agg = SPEC.aggregate || {};
  $('#verdicts').innerHTML = (SPEC.layers || []).map(l => {
    const a = agg[l.id] || {};
    const r = { differ: a.differ||0, na: a.not_applicable||0,
               refused: a.refused||0, rated: a.rated||0 };
    return `<div class="vcard"><h3>${dotSpan(aggDot(r))}${l.id} ${l.name}</h3>`
         + `${verdicts[l.id] || ''}</div>`;
  }).join('');
}

function drawTrend(){
  $('#trend').innerHTML = SPEC.trend || '';
}

function histArrow(key){
  return histSort.key === key ? (histSort.dir === 'asc' ? ' &#9650;' : ' &#9660;') : '';
}

function sortHist(key){
  if(histSort.key === key) histSort.dir = histSort.dir === 'asc' ? 'desc' : 'asc';
  else histSort = { key, dir: key === 'when' ? 'desc' : 'asc' };
  histPage = 0;
  drawHist();
}

function drawHist(){
  const all = histFiltered().sort(histCompare(histSort.key, histSort.dir));
  const pages = Math.max(1, Math.ceil(all.length / HIST_PAGE_SIZE));
  histPage = Math.min(Math.max(0, histPage), pages - 1);
  const start = histPage * HIST_PAGE_SIZE;
  const page = all.slice(start, start + HIST_PAGE_SIZE);
  const total = (SPEC.runs || []).length;

  $('#hist').innerHTML =
    `<tr><th class="sortable" onclick="sortHist('when')">When${histArrow('when')}`
    + `<th class="sortable" onclick="sortHist('run')">Run${histArrow('run')}`
    + `<th class="sortable" onclick="sortHist('class')">Class${histArrow('class')}`
    + `<th class=n>Agree<th class=n>Differ</tr>` +
    page.map(e =>
      `<tr><td class=det>${(e.at||'').replace('T',' ').slice(5,16)}`
      + `<td>${dotSpan(histDot(e))}<a href="/runs/${e.file}" target="_blank">${e.layer} ${e.name}</a>`
      + (e.partial ? '<span class="tag">partial</span>' : '')
      + reviewTag(e)
      + `<td>${e.class_code||'--'}<td class=n>${e.agree||0}`
      + `<td class=n>${e.differ||0}</tr>`).join('')
    || '<tr><td colspan=5 class="det">no runs match this filter</td></tr>';

  $('#histpg').innerHTML = all.length ?
    `<button class="ghost" id="histprev"${histPage===0?' disabled':''}>&larr; Prev</button>`
    + `<span>Page ${histPage+1} of ${pages} &middot; ${all.length}`
    + (all.length !== total ? ` of ${total}` : '') + ` runs</span>`
    + `<button class="ghost" id="histnext"${histPage>=pages-1?' disabled':''}>Next &rarr;</button>`
    : '';
  if($('#histprev')) $('#histprev').onclick = () => { histPage--; drawHist(); };
  if($('#histnext')) $('#histnext').onclick = () => { histPage++; drawHist(); };
}

async function refresh(){
  SPEC = await get('/api/tests/spec');
  $('#tick').textContent = SPEC.spent_today;
  histPage = 0;                       // a run just finished; show the newest
  populateHistFilters();
  drawHist();
  drawAgg();
  drawVerdicts();
  drawTrend();
}

(async () => {
  SPEC = await get('/api/tests/spec');
  $('#tick').textContent = SPEC.spent_today;
  drawLayers(); syncClassCard(); drawCount();
  await loadBases(); await refresh();
  $('#basis').onchange = loadClasses;
  $('#filter').oninput = drawClasses;
  // Anything that changes the number of tests redraws it. The estimate is
  // local arithmetic, so this costs nothing and never lags the typing.
  ['#allowance', '#offline', '#cls', '#exposure'].forEach(sel => {
    $(sel).oninput = () => drawCount();
    $(sel).onchange = () => drawCount();
  });
})();
</script></body></html>
"""
