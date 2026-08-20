"""The variable tester: pick values from dropdowns, run all 51, read the result.

Mounted by `app.py` at `/tester`. Everything here is presentation, persistence
and progress. **It decides nothing about insurance:** legal values come from
`variants`, premiums from `gl_engine`, agreement from
`phase2_compare.compare_payload`.

    from ui import tester
    tester.dispatch("GET", "/api/tester/spec", {}, None)

### Three decisions the page makes visible rather than hiding

* **The measurement is our premium against ISO's**, so the comparison is on by
  default and the results table leads with those two numbers and the difference
  between them. It still **says how many live calls it will make before it
  makes them** -- one per jurisdiction, about twenty minutes for a full sweep --
  and unticking it gives the free engine-only run for iterating on dropdowns.
  *Whether a configuration moved the premium away from the unvaried base is a
  property of the configuration, not a result; it is a marker on the engine
  figure and a footnote, not a column competing with the comparison.*
* **A jurisdiction that cannot express the configuration is grey, not red.** NY
  declares no claims-made form; 20 jurisdictions declare one prem/ops
  territory. `NOT APPLICABLE` is a third outcome and the page keeps it visually
  distinct from disagreement, because merging them would report twenty failures
  for a risk ISO never permitted.
* **A run that does not move the premium is called out.** Agreement on an
  unchanged number proves the two engines can both do nothing.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import variants as V                                          # noqa: E402
import sweep                                                  # noqa: E402
from raas import NO_ISO                                       # noqa: E402
import runstore as store                                      # noqa: E402

from . import charts, variables                        # noqa: E402

#: Seconds per live ISO call, measured over the phase 2 runs. Used only to warn
#: before a long run -- a twenty-minute wait a person did not expect is the
#: complaint this number exists to prevent.
SECONDS_PER_CALL = 20

JOBS: dict = {}
JOBS_LOCK = threading.Lock()


def _engine_version() -> str:
    """Asked of `sweep`, never of the engine -- see `ui/__init__.py`."""
    try:
        return sweep.engine_version()
    except Exception:                                         # noqa: BLE001
        return ""


def _worker(job_id: str, config: dict, jurisdictions, compare: bool,
            mode: str, label: str) -> None:
    def progress(done, total, row):
        with JOBS_LOCK:
            job = JOBS[job_id]
            job["done"] = done
            job["total"] = total
            job["rows"].append(row)

    try:
        out = sweep.run_config(config, jurisdictions, compare=compare,
                               mode=mode, progress=progress)
    except Exception as exc:                                  # noqa: BLE001
        with JOBS_LOCK:
            JOBS[job_id].update(finished=True, error=f"{type(exc).__name__}: {exc}")
        return
    line = store.append(out["summary"], out["rows"],
                        engine_version=_engine_version(), label=label)
    with JOBS_LOCK:
        JOBS[job_id].update(finished=True, summary=out["summary"],
                            rows=out["rows"], run_id=line["id"])


# ------------------------------------------------------------------ handlers

def _spec(query) -> tuple:
    refresh = query.get("refresh") in ("1", "true")
    spec = variables.specs(refresh=refresh)
    return 200, json.dumps({**spec, "no_iso": sorted(NO_ISO),
                            "seconds_per_call": SECONDS_PER_CALL}), "json"


def _options(body) -> tuple:
    juris = (body.get("juris") or "").upper()
    if juris not in V.Declared.jurisdictions():
        return 400, json.dumps({"error": f"no base submission for {juris!r}"}), "json"
    return 200, json.dumps(variables.for_juris(juris, body.get("config") or {})), "json"


def _legality(body) -> tuple:
    cfg = V.clean(body.get("config") or {})
    out = variables.legality(cfg)
    out["describes"] = V.describe(cfg)
    out["fingerprint"] = V.fingerprint(cfg)
    return 200, json.dumps(out), "json"


def _start_run(body) -> tuple:
    cfg = V.clean(body.get("config") or {})
    mode = body.get("mode") or "strict-erc"
    compare = bool(body.get("compare"))
    js = body.get("jurisdictions") or list(V.Declared.jurisdictions())
    js = [j.upper() for j in js]
    if compare:
        js = [j for j in js if j not in NO_ISO]
    if not js:
        return 400, json.dumps({"error": "no jurisdictions to run"}), "json"
    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {"id": job_id, "total": len(js), "done": 0, "rows": [],
                        "finished": False, "compare": compare,
                        "config": cfg, "describes": V.describe(cfg),
                        "started": time.time()}
    threading.Thread(target=_worker, daemon=True,
                     args=(job_id, cfg, js, compare, mode,
                           body.get("label") or "")).start()
    return 200, json.dumps({"id": job_id, "total": len(js), "compare": compare,
                            "estimate_seconds": len(js) * SECONDS_PER_CALL
                            if compare else len(js) * 2}), "json"


def _qa_spec(query=None) -> tuple:
    """The tiers, what each costs, and how much budget is left today.

    Everything here is computed by `scripts/qa.py`, which is the single
    definition of a tier. A second list of tiers maintained next to the first
    would drift, and the drift would look like a rating defect -- the same
    argument that keeps one definition of "agree".
    """
    import qa
    tiers = []
    for key in sorted(qa.TIERS):
        spec = qa.TIERS[key]
        row = {"id": key, "name": spec["name"], "what": spec["what"],
               "runnable": spec["build"] is not None}
        if row["runnable"]:
            row.update(qa.cost(key))
        tiers.append(row)
    spent = qa._spent_today()
    return 200, json.dumps({
        "tiers": tiers,
        "core": list(qa.CORE),
        "why_core": qa.WHY_CORE,
        "budget": {"spent_today": spent,
                   "standing": qa.DAILY_STANDING,
                   "ceiling": qa.DAILY_CEILING,
                   "remaining": max(0, qa.DAILY_STANDING - spent)},
        "seconds_per_call": qa.SECONDS_PER_LIVE_CALL,
    }), "json"


def _qa_summary(query) -> tuple:
    """The one-screen answer: a verdict, a map, and what changed since last time."""
    tier = (query or {}).get("tier") or ""
    if isinstance(tier, list):
        tier = tier[0] if tier else ""
    roll = store.qa_rollup(tier)
    c = roll["counts"]
    return 200, json.dumps({
        **roll,
        "verdict": charts.verdict(
            agree=c["agrees"], differs=c["differs"],
            not_applicable=c["not_applicable"], refused=c["refused"],
            uncompared=c["uncompared"]),
        "map": charts.usa_map(roll["status"]),
    }), "json"


def _qa_review(query) -> tuple:
    """What the harness found when it reviewed its own results.

    **A reader, not a workflow.** Pass 3's verdicts are computed here and are
    definitive. Pass 4's briefs are *questions*, and the answers come from
    specialist agents a person dispatches -- the server cannot invoke them, and
    a screen that implied otherwise would be claiming a review had happened when
    it had not.
    """
    import qa_review as QR
    tier = (query or {}).get("tier") or ""
    if isinstance(tier, list):
        tier = tier[0] if tier else ""
    limit = 30

    pass3 = QR.review_runs(tier, "", limit)
    briefs = QR.briefs_for_run(tier, limit)

    # Group the briefs by the question they ask, because twenty scenarios
    # asking one question is one thing to look at, not twenty.
    by_kind: dict = {}
    for b in briefs:
        head = b["claim"].split(" in ")[0][:70]
        by_kind.setdefault(head, {"claim": b["claim"], "n": 0, "states": set(),
                                  "question": b["question"],
                                  "reviewers": sorted(b["prompts"])})
        g = by_kind[head]
        g["n"] += 1
        j = b["evidence"].get("jurisdiction")
        if j:
            g["states"].add(j)
    groups = sorted(by_kind.values(), key=lambda g: -g["n"])
    for g in groups:
        g["states"] = sorted(g["states"])

    # Refused payloads already on disk, if they have been exported.
    payloads = []
    d = QR.REFUSED_DIR
    if d.is_dir():
        payloads = sorted(x.name for x in d.iterdir() if x.is_dir())

    return 200, json.dumps({
        "pass3": {"reviewed": pass3["reviewed"], "counts": pass3["counts"],
                  "contradicted": [
                      {"juris": x["juris"],
                       "describes": V.describe(x["config"]),
                       "why": next((f["why"] for f in x["findings"]
                                    if f["verdict"] == QR.CONTRADICTED), "")}
                      for x in pass3["results"]
                      if x["verdict"] == QR.CONTRADICTED][:20],
                  "causes": _pass3_causes(pass3)},
        "briefs": groups,
        "payload_dir": str(d),
        "payloads": payloads,
    }), "json"


def _pass3_causes(pass3) -> list:
    """The distinct reasons a jurisdiction could not express a configuration."""
    seen: dict = {}
    for x in pass3["results"]:
        c = x.get("cause")
        if not c:
            continue
        seen.setdefault(c["why"][:110], {"why": c["why"][:110], "n": 0,
                                         "states": set()})
        seen[c["why"][:110]]["n"] += 1
        seen[c["why"][:110]]["states"].add(x["juris"])
    out = sorted(seen.values(), key=lambda g: -g["n"])
    for g in out:
        g["states"] = sorted(g["states"])
    return out[:12]


def _qa_plan(body) -> tuple:
    """The matrix a tier would run, without running it -- the button's `--plan`."""
    import qa
    tier = (body or {}).get("tier")
    if tier not in qa.TIERS:
        return 400, json.dumps({"error": "unknown tier"}), "json"
    if qa.TIERS[tier]["build"] is None:
        return 400, json.dumps({"error": f"{tier} is not built",
                                "why": qa.TIERS[tier]["what"]}), "json"
    js = (body or {}).get("jurisdictions") or None
    offline = bool((body or {}).get("offline"))
    sc = qa.scenarios_for(tier, js)
    return 200, json.dumps({
        "tier": tier,
        "cost": qa.cost(tier, js, offline),
        "scenarios": [{"describes": V.describe(c) or "the base risk, unvaried",
                       "config": c, "jurisdictions": j} for c, j in sc],
    }), "json"


def _qa_start(body) -> tuple:
    """Start a whole tier. Unlike a single run, this walks many scenarios.

    **The budget guard is enforced here, not only in the CLI.** A button that
    could spend more than the standing budget while the command line refused
    would make the budget a matter of which door you came in by.
    """
    import qa
    body = body or {}
    tier = body.get("tier")
    if tier not in qa.TIERS:
        return 400, json.dumps({"error": "unknown tier"}), "json"
    spec = qa.TIERS[tier]
    if spec["build"] is None:
        return 400, json.dumps({"error": f"{tier} is not built",
                                "why": spec["what"]}), "json"

    offline = bool(body.get("offline"))
    js = body.get("jurisdictions") or None
    sc = qa.scenarios_for(tier, js)
    cost = qa.cost(tier, js, offline)

    forced = bool(body.get("force"))
    label_extra = ""
    if not offline:
        b = qa._budget_check(cost["live_calls"], forced)
        if not b["ok"] and not forced:
            # 409, not 429: this is a warning the caller can act on, not a
            # refusal. The budget is our own policy and the person holding the
            # subscription is better placed to weigh one run than a constant is.
            return 409, json.dumps({
                "warning": "over the daily live-call budget",
                "budget": b,
                "detail": b["why"],
                "confirm": "send the same request with force: true to run it"
            }), "json"
        if not b["ok"]:
            label_extra = " [OVER BUDGET, forced]"

    job_id = uuid.uuid4().hex[:12]
    total = sum(len(j) for _, j in sc)
    with JOBS_LOCK:
        JOBS[job_id] = {"id": job_id, "qa": tier, "total": total, "done": 0,
                        "rows": [], "finished": False, "compare": not offline,
                        "scenarios": len(sc), "scenario_done": 0,
                        "describes": f"{tier} -- {spec['name']}",
                        "config": {}, "started": time.time(),
                        "findings": [], "forced": bool(label_extra)}
    threading.Thread(target=_qa_worker, daemon=True,
                     args=(job_id, tier, sc, offline,
                           body.get("mode") or "strict-erc",
                           label_extra)).start()
    return 200, json.dumps({
        "id": job_id, "tier": tier, "total": total, "scenarios": len(sc),
        "compare": not offline,
        "estimate_seconds": cost["live_seconds"] if not offline
        else cost["offline_seconds"]}), "json"


def _qa_worker(job_id, tier, scenarios, offline, mode, label_extra=""):
    agree = differ = na = stopped = calls = 0
    findings = []
    for idx, (cfg, js) in enumerate(scenarios, 1):
        def progress(done, total, row, _idx=idx):
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                if job is None:
                    return
                job["done"] += 1
                job["scenario_done"] = _idx
                job["rows"].append(row)
        try:
            out = sweep.run_config(cfg, js, compare=not offline, mode=mode,
                                   progress=progress)
        except Exception as exc:                              # noqa: BLE001
            findings.append({"kind": "run failed",
                             "describes": V.describe(cfg),
                             "detail": f"{type(exc).__name__}: {exc}"[:200]})
            continue
        s = out["summary"]
        agree += s["agree"]
        differ += len(s["differ"]) + len(s["premium_only"])
        na += len(s["not_applicable"])
        stopped += len(s["engine_stopped"])
        calls += s["live_calls"]
        store.append(s, out["rows"], label=f"qa {tier}{label_extra}")

        # Findings are collected as the run goes, so a long tier is useful
        # before it finishes rather than only after.
        for j in s["differ"] + s["premium_only"]:
            findings.append({"kind": "disagrees with ISO", "juris": j,
                             "describes": V.describe(cfg)})
        for row in out["rows"]:
            v = (row.get("no_op") or {})
            if v.get("verdict") == "INERT VALUE":
                findings.append({
                    "kind": "exercised nothing", "juris": row["juris"],
                    "describes": V.describe(cfg),
                    "detail": f"{v.get('column')}={v.get('chosen')} does "
                              f"nothing; {v.get('moves_with')} gives "
                              f"{v.get('premium')}"})
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job is not None:
            job["finished"] = True
            job["findings"] = findings
            job["summary"] = {
                "tier": tier, "scenarios": len(scenarios), "agree": agree,
                "differ": differ, "not_applicable": na, "engine_stopped": stopped,
                "live_calls": calls,
                "seconds": round(time.time() - job["started"], 1)}


def _run_state(job_id: str) -> tuple:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return 404, json.dumps({"error": "no such run"}), "json"
        out = dict(job)
        out["rows"] = list(job["rows"])
    if out.get("summary"):
        out["bars"] = charts.status_bars(out["summary"])
    return 200, json.dumps(out), "json"


def _history() -> tuple:
    series = store.history()
    return 200, json.dumps({
        "runs": store.runs(limit=60),
        "series": series,
        "chart": charts.agreement_over_time(series),
    }), "json"


def _coverage() -> tuple:
    cov = store.coverage()
    spec = variables.specs()
    controls = [{"id": c["id"], "label": c["label"]} for c in spec["controls"]]
    return 200, json.dumps({
        **cov,
        "chart": charts.coverage_grid(controls, spec["jurisdictions"],
                                     cov["rated"], cov["declined"]),
        "exercised": sum(1 for c in controls if cov["rated"].get(c["id"])),
        "controls": len(controls),
    }), "json"


def _curve(control_id: str) -> tuple:
    if control_id not in V.BY_ID:
        return 404, json.dumps({"error": f"unknown control {control_id!r}"}), "json"
    series = store.response_curve(control_id)
    # **Report what can be DRAWN, not what was stored.** A curve needs two
    # values of the same control in the same jurisdiction; counting the 51 that
    # have one apiece produced "51 jurisdictions" above an empty chart on the
    # first run of this endpoint.
    drawable = sum(1 for pts in series.values() if len(pts) >= 2)
    return 200, json.dumps({
        "control": control_id,
        "label": V.BY_ID[control_id].label,
        "jurisdictions": drawable,
        "with_any_value": len(series),
        "values_seen": sorted({p["value"] for pts in series.values()
                               for p in pts}),
        "chart": charts.response_curve(V.BY_ID[control_id].label, series),
    }), "json"


def _defects() -> tuple:
    return 200, json.dumps({"defects": store.defects()}), "json"


def dispatch(method: str, path: str, query: dict, body):
    """Handle a tester route, or return None so the caller keeps looking.

    The layered test page is tried first. It is a separate module with separate
    routes and it shares nothing with the tier runner below except the run
    store -- mounting it here rather than in `app.py` keeps that file's mount at
    four lines, which was the point of the boundary.
    """
    from . import tests_page
    out = tests_page.dispatch(method, path, query, body)
    if out is not None:
        return out
    if path == "/tester" and method == "GET":
        return 200, PAGE, "html"
    if not path.startswith("/api/tester"):
        return None
    if method == "GET":
        if path == "/api/tester/spec":
            return _spec(query)
        if path == "/api/tester/history":
            return _history()
        if path == "/api/tester/coverage":
            return _coverage()
        if path == "/api/tester/defects":
            return _defects()
        if path == "/api/tester/qa":
            return _qa_spec(query)
        if path == "/api/tester/qa/summary":
            return _qa_summary(query)
        if path == "/api/tester/qa/review":
            return _qa_review(query)
        if path.startswith("/api/tester/curve/"):
            return _curve(unquote(path.rsplit("/", 1)[-1]))
        if path.startswith("/api/tester/run/"):
            return _run_state(path.rsplit("/", 1)[-1])
        return 404, json.dumps({"error": "not found"}), "json"
    if method == "POST":
        body = body or {}
        if path == "/api/tester/options":
            return _options(body)
        if path == "/api/tester/legality":
            return _legality(body)
        if path == "/api/tester/run":
            return _start_run(body)
        if path == "/api/tester/qa/plan":
            return _qa_plan(body)
        if path == "/api/tester/qa/run":
            return _qa_start(body)
        return 404, json.dumps({"error": "not found"}), "json"
    return None


# ---------------------------------------------------------------------- page

PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>Variable tester -- GL rating engine</title>
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
nav{margin-left:auto;display:flex;gap:6px}
nav a{font-size:13px;text-decoration:none;color:var(--blue);padding:5px 10px;
border:1px solid var(--line);border-radius:6px;background:#fff}
nav a.on{background:var(--blue);color:#fff;border-color:var(--blue)}
main{padding:16px 20px;display:grid;grid-template-columns:340px 1fr;gap:16px;
align-items:start}
@media(max-width:900px){main{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;
padding:13px 14px;margin-bottom:14px}
.card h2{font-size:12px;text-transform:uppercase;letter-spacing:.05em;
color:var(--muted);margin:0 0 9px;font-weight:650}
.grp{margin-bottom:11px}
.grp h3{font-size:12.5px;margin:0 0 6px;color:var(--ink);font-weight:650}
label{display:block;font-size:12px;color:var(--muted);margin:6px 0 2px}
select,input[type=number],input[type=text]{width:100%;padding:5px 7px;
border:1px solid #cbd2d9;border-radius:5px;font-size:12.5px;background:#fff;
color:var(--ink)}
select:disabled{background:#f0f3f6;color:var(--muted)}
button{background:var(--blue);color:#fff;border:0;border-radius:6px;
padding:8px 13px;font-size:13px;font-weight:600;cursor:pointer}
button.ghost{background:#fff;color:var(--ink);border:1px solid #cbd2d9;
font-weight:500}
button:disabled{opacity:.55;cursor:default}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:9px}
.hint{font-size:11.5px;color:var(--muted);margin-top:5px}
.warn{font-size:11.5px;color:var(--amber);margin-top:5px}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;font-weight:650;color:var(--muted);font-size:11px;
text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--line);
padding:5px 6px}
td{padding:4px 6px;border-bottom:1px solid #f0f3f6;vertical-align:top}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.st{font-weight:650;font-size:11.5px;white-space:nowrap}
.st.MATCH,.st.RATED{color:var(--blue)}
.st.DIFF,.st\.ENGINE{color:var(--red)}
.bad{color:var(--red);font-weight:650}
.na{color:var(--grey);font-weight:650}
.am{color:var(--amber);font-weight:650}
.det{color:var(--muted);font-size:11.5px}
.bar{height:7px;background:#eef2f6;border-radius:99px;overflow:hidden;margin:9px 0}
.bar>div{height:100%;background:var(--blue);width:0;transition:width .25s}
.scroll{max-height:460px;overflow:auto}
.tabs{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap}
.tabs button{background:#fff;color:var(--ink);border:1px solid #cbd2d9;
font-weight:500}
.tabs button.on{background:var(--blue);color:#fff;border-color:var(--blue);
font-weight:650}
code{background:#f0f3f6;padding:1px 4px;border-radius:3px;font-size:11.5px}
.note{font-size:11.5px;color:var(--muted);border-left:2px solid var(--line);
padding-left:8px;margin-top:5px}
.qat{border:1px solid var(--line);border-radius:6px;padding:7px 10px;margin:5px 0;
cursor:pointer;background:#fff;display:block}
.qat.on{border-color:var(--blue);box-shadow:0 0 0 1px var(--blue) inset}
.qat.off{opacity:.5;cursor:not-allowed}
.qat b{display:block;font-size:13px}
.qat span{display:block;font-size:11.5px;color:var(--blue);margin-top:1px}
.qat i{display:block;font-size:11px;color:var(--muted);font-style:normal;margin-top:2px}
#qaprog{height:100%;width:0;background:var(--blue);transition:width .3s}
</style></head><body>
<header>
  <h1>Variable tester</h1>
  <span class="sub" id="sub">loading ISO's declared options...</span>
  <nav><a href="/">Rate one submission</a><a href="/tester" class="on">Variable tester</a><a href="/tests">Layered tests</a><a href="/runs/index.html" target="_blank">Run files</a></nav>
</header>
<main>
 <div>
  <div class="card" id="qacard">
   <h2>QA programme</h2>
   <div class="hint">Whole tiers, sized from ISO's own declared content. The
     cost is shown <b>before</b> the button, and a tier over the daily
     live-call budget refuses to start.</div>
   <div id="qatiers"></div>
   <label style="margin-top:10px"><input type="checkbox" id="qalive" checked>
     Compare each against ISO</label>
   <div class="row" style="margin-top:8px">
     <button id="qarun">Start</button>
     <button class="ghost" id="qaplan">Show the matrix first</button>
   </div>
   <div class="hint" id="qabudget"></div>
   <div class="bar"><div id="qaprog"></div></div>
   <div class="hint" id="qastatus"></div>
  </div>
  <div class="card">
   <h2>The risk</h2>
   <div id="controls"></div>
   <div class="row">
     <button id="run">Run all states</button>
     <button class="ghost" id="check">Check where it applies</button>
     <button class="ghost" id="reset">Reset</button>
   </div>
   <label style="margin-top:10px"><input type="checkbox" id="compare" checked>
     Compare each against ISO</label>
   <div class="hint" id="cost"></div>
   <div class="bar"><div id="prog"></div></div>
   <div class="hint" id="status">Every option below is read from ISO's own
     domain tables, per jurisdiction. A value this base cannot express is
     refused before anything is sent.</div>
  </div>
 </div>
 <div>
  <div class="card">
    <h2>This run</h2>
    <div id="summary" class="hint">Nothing run yet. The test is
      <b>our premium against ISO's</b>, jurisdiction by jurisdiction — leave
      every control blank to run the unvaried base risk.</div>
    <div id="bars"></div>
    <div class="scroll"><table id="rows"></table></div>
  </div>
  <div class="card">
    <h2>Over time</h2>
    <div class="tabs" id="views"></div>
    <div id="view"></div>
  </div>
 </div>
</main>
<script>
const $=id=>document.getElementById(id);
let QA=null, QATIER=null, QAJOB=null, QATIMER=null;

// ---- QA programme. Every figure comes from /api/tester/qa, which computes it
// ---- from scripts/qa.py. Nothing about a tier is defined twice.
function qaLoad(){
  fetch('/api/tester/qa').then(r=>r.json()).then(d=>{
    QA=d;
    if(!QATIER){const f=d.tiers.find(t=>t.id==='T1'&&t.runnable)||d.tiers.find(t=>t.runnable);
      QATIER=f?f.id:null;}
    qaTiers(); qaBudget();
  }).catch(()=>{});
}
function qaTiers(){
  $('qatiers').innerHTML=QA.tiers.map(t=>{
    const on=t.id===QATIER, dis=!t.runnable;
    const cost=t.runnable
      ? t.scenarios+' scenarios &middot; '+t.live_calls+' ISO calls &middot; '
        +Math.round(t.live_seconds/60)+' min'
      : 'not built';
    return '<div class="qat'+(on?' on':'')+(dis?' off':'')+'" data-t="'+t.id+'">'
      +'<b>'+t.id+' &middot; '+esc(t.name)+'</b>'
      +'<span>'+cost+'</span>'
      +'<i>'+esc(t.what)+'</i></div>';
  }).join('');
  document.querySelectorAll('.qat').forEach(el=>{
    if(el.classList.contains('off'))return;
    el.onclick=()=>{QATIER=el.dataset.t;QAARMED=false;
      $('qarun').textContent='Start';$('qarun').style.background='';
      qaTiers();qaBudget();};
  });
}
function qaBudget(){
  const b=QA.budget, t=QA.tiers.find(x=>x.id===QATIER);
  const live=$('qalive').checked;
  let msg='<b>'+b.spent_today+'</b> of '+b.standing+' live calls spent today &middot; '
    +'<b>'+b.remaining+'</b> remain (ceiling '+b.ceiling+').';
  if(t&&t.runnable&&live){
    msg+=' This tier needs <b>'+t.live_calls+'</b>.';
    if(t.live_calls>b.remaining)
      msg+=' <b style="color:var(--red)">Over budget \u2014 it warns first, '
        +'and you can override.</b>';
  } else if(live===false){ msg+=' <b>Offline \u2014 free, no calls.</b>'; }
  $('qabudget').innerHTML=msg;
}
function qaPlan(){
  $('qastatus').textContent='building the matrix\u2026';
  fetch('/api/tester/qa/plan',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({tier:QATIER,offline:!$('qalive').checked})})
   .then(r=>r.json()).then(d=>{
     if(d.error){$('qastatus').textContent=d.error+(d.why?' \u2014 '+d.why:'');return;}
     $('qastatus').innerHTML='<b>'+d.scenarios.length+' scenarios</b>, nothing run:'
       +'<ol style="margin:6px 0 0 18px;padding:0">'
       +d.scenarios.map(x=>'<li>'+esc(x.describes)+' <span style="color:var(--muted)">&rarr; '
         +x.jurisdictions.length+' jurisdictions</span></li>').join('')+'</ol>';
   });
}
let QAARMED=false;
function qaRun(){
  const offline=!$('qalive').checked;
  $('qastatus').textContent='starting\u2026';
  fetch('/api/tester/qa/run',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({tier:QATIER,offline:offline,force:QAARMED})})
   .then(r=>r.json().then(d=>({code:r.status,d:d}))).then(({code,d})=>{
     if(code===409){
       // A warning you can act on, not a refusal. Arm the button rather
       // than pop a dialog: the second click is then a deliberate choice,
       // and the number stays on screen while you make it.
       const b=d.budget;
       QAARMED=true;
       $('qarun').textContent='Run anyway \u2014 '+b.over_by+' over budget';
       $('qarun').style.background='var(--red)';
       $('qastatus').innerHTML='<b style="color:var(--red)">Over budget.</b> '
         +esc(d.detail)+'<br><b>Nothing was sent.</b> Press the red button '
         +'to run it anyway, or untick <i>Compare each against ISO</i> to '
         +'run it free. The budget is <b>our own policy</b>, not a limit '
         +'ISO publishes \u2014 it exists so our traffic keeps looking like '
         +'ordinary use.';
       return;
     }
     if(d.error){$('qastatus').textContent=d.error+(d.why?' \u2014 '+d.why:'');return;}
     QAARMED=false;
     $('qarun').textContent='Start';
     $('qarun').style.background='';
     QAJOB=d.id;
     $('qastatus').textContent=d.tier+' running \u2014 '+d.scenarios+' scenarios, '
       +d.total+' ratings'+(offline?', offline':', '+d.total+' ISO calls');
     if(QATIMER)clearInterval(QATIMER);
     QATIMER=setInterval(qaPoll,900); qaPoll();
   });
}
function qaPoll(){
  if(!QAJOB)return;
  fetch('/api/tester/run/'+QAJOB).then(r=>r.json()).then(j=>{
    const pct=j.total?Math.round(100*j.done/j.total):0;
    $('qaprog').style.width=pct+'%';
    let msg='scenario <b>'+(j.scenario_done||0)+'</b> of '+j.scenarios
      +' &middot; '+j.done+' of '+j.total+' ratings';
    if(j.finished){
      clearInterval(QATIMER);QATIMER=null;
      const s=j.summary||{};
      msg='<b>'+j.qa+' complete</b> in '+Math.round((s.seconds||0)/60)+' min &middot; '
        +'agree '+(s.agree||0)+' &middot; disagree <b>'+(s.differ||0)+'</b> &middot; '
        +'not applicable '+(s.not_applicable||0)+' &middot; refused '
        +(s.engine_stopped||0)+' &middot; '+(s.live_calls||0)+' ISO calls';
      if(j.findings&&j.findings.length)
        msg+='<ol style="margin:6px 0 0 18px;padding:0">'+j.findings.slice(0,12).map(f=>
          '<li><b>'+esc(f.kind)+'</b>'+(f.juris?' &middot; '+esc(f.juris):'')+' &middot; '
          +esc(f.describes||'')+(f.detail?'<br><span style="color:var(--muted)">'
          +esc(f.detail)+'</span>':'')+'</li>').join('')+'</ol>';
      else if(j.finished) msg+='<br><b>No findings.</b>';
      qaLoad();
    }
    $('qastatus').innerHTML=msg;
  });
}

let SPEC=null, CONFIG={}, JOB=null, TIMER=null;
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// ---- the control panel. Options come from the spec; nothing is hardcoded.
function panel(){
  const byGroup={};
  SPEC.controls.forEach(c=>{(byGroup[c.group]=byGroup[c.group]||[]).push(c)});
  let h='';
  SPEC.groups.forEach(g=>{
    h+='<div class="grp"><h3>'+esc(g)+'</h3>';
    byGroup[g].forEach(c=>{
      h+='<label title="'+esc(c.exercises)+'">'+esc(c.label);
      if(c.keyed_by.length) h+=' <span style="color:var(--blue)">·keyed</span>';
      h+='</label>';
      if(c.kind==='number'){
        const mx=c.max?(' max="'+c.max+'"'):'';
        h+='<input type="number" id="c_'+c.id+'" min="0"'+mx+
           ' placeholder="unchanged">';
      }else{
        h+='<select id="c_'+c.id+'"><option value="">unchanged</option>'+
          c.values.map(v=>{
            const partial=!v.everywhere;
            const un=(c.unbuildable||[]).includes(v.value);
            return '<option value="'+esc(v.value)+'"'+(un?' data-un="1"':'')+'>'+
              esc(v.value)+(un?'  — needs its own base':
                (partial?'  — '+v.states.length+'/'+SPEC.jurisdictions.length+' states':''))+
              '</option>';
          }).join('')+'</select>';
      }
      if(c.note) h+='<div class="note">'+esc(c.note)+'</div>';
    });
    h+='</div>';
  });
  $('controls').innerHTML=h;
  SPEC.controls.forEach(c=>{
    $('c_'+c.id).onchange=()=>{
      const v=$('c_'+c.id).value;
      if(v==='') delete CONFIG[c.id]; else CONFIG[c.id]=v;
      cost(); refreshKeyed(c.id);
    };
  });
}

// A control whose domain is keyed on another must be re-read when that other
// changes -- the combined deductible collapses to No Deductible once BI or PD
// is set, and offering the stale 31 would be offering illegal values.
function refreshKeyed(changed){
  const dependents=SPEC.controls.filter(c=>c.keyed_by.includes(changed));
  if(!dependents.length) return;
  const juris=SPEC.jurisdictions.includes('OK')?'OK':SPEC.jurisdictions[0];
  post('/api/tester/options',{juris:juris,config:CONFIG}).then(j=>{
    dependents.forEach(c=>{
      const spec=j.controls[c.id]; if(!spec||spec.kind!=='select') return;
      const sel=$('c_'+c.id), was=sel.value;
      sel.innerHTML='<option value="">unchanged</option>'+
        spec.values.map(v=>'<option value="'+esc(v)+'">'+esc(v)+'</option>').join('');
      if(spec.values.includes(was)) sel.value=was;
      else if(was){ delete CONFIG[c.id];
        note(c.label+' was reset: with '+changed.replace(/_/g,' ')+' set, ISO '+
             'declares only '+spec.values.length+' legal value(s) for it.'); }
    });
  });
}
function note(m){ $('status').innerHTML=esc(m); }

function cost(){
  const n=SPEC.jurisdictions.length, iso=n-SPEC.no_iso.filter(
    j=>SPEC.jurisdictions.includes(j)).length;
  if($('compare').checked){
    const mins=Math.round(iso*SPEC.seconds_per_call/60);
    $('cost').innerHTML='<span class="warn">'+iso+' live calls to ISO, about '+
      mins+' minute'+(mins===1?'':'s')+'. '+
      esc(SPEC.no_iso.join(', '))+' is not on the subscription and is left out.'+
      '</span>';
  } else {
    // The FIRST run also rates each jurisdiction's unvaried base, once, so
    // "moved from base" costs nothing afterwards. Quoting the steady-state
    // number to someone about to wait twice that is the kind of small
    // dishonesty this tool is supposed to be the opposite of.
    $('cost').innerHTML=n+' jurisdictions, engine only. No calls, about '+
      Math.round(n*1.7)+'s &mdash; roughly double on the first run, which also '+
      'rates each unvaried base once and keeps it.';
  }
}

// ---- running
function run(){
  $('run').disabled=true; $('rows').innerHTML=''; $('bars').innerHTML='';
  $('summary').textContent='starting...';
  post('/api/tester/run',{config:CONFIG,compare:$('compare').checked})
    .then(j=>{ JOB=j.id; poll(); })
    .catch(e=>{ $('summary').innerHTML='<span class="bad">'+esc(e)+'</span>';
                $('run').disabled=false; });
}
function poll(){
  fetch('/api/tester/run/'+JOB).then(r=>r.json()).then(j=>{
    $('prog').style.width=(100*j.done/Math.max(1,j.total))+'%';
    $('summary').textContent=j.describes||'the base risk, unvaried';
    rows(j.rows||[]);
    if(j.error){ $('summary').innerHTML='<span class="bad">'+esc(j.error)+
      '</span>'; $('run').disabled=false; return; }
    if(j.finished){
      $('run').disabled=false; $('bars').innerHTML=j.bars||'';
      summarise(j.summary); loadView(CURRENT); return;
    }
    TIMER=setTimeout(poll, 700);
  });
}
const CLS={'MATCH':'st MATCH','RATED':'st RATED','DIFF':'bad',
  'PREMIUM ONLY':'am','NOT APPLICABLE':'na','ENGINE STOPPED':'bad',
  'ENGINE ERROR':'bad','BUILD ERROR':'bad','RAAS FAILED':'bad'};

// **The measurement is our premium against ISO's.** Those two columns and the
// difference between them are the table; everything else is context for a row
// that does not have them. Whether the premium moved from the unvaried base is
// a property of the CONFIGURATION, not a test result, so it is a marker on the
// engine figure rather than a column competing with the comparison.
function rows(rs){
  if(!rs.length){ $('rows').innerHTML=''; return; }
  let h='<tr><th>State</th><th>Engine premium</th><th>ISO premium</th>'+
    '<th>Difference</th><th>Outcome</th><th></th></tr>';
  rs.forEach(r=>{
    const d=r.delta==null?'':String(r.delta);
    const zero=(d===''||Number(d)===0);
    h+='<tr><td>'+esc(r.juris)+'</td>'+
      '<td class="n">'+esc(r.ours||'—')+
        (r.moved===false?' <span class="am" title="this configuration did not'+
          ' change the premium in this state">·</span>':'')+'</td>'+
      '<td class="n">'+(r.iso!=null?esc(r.iso):
        '<span class="det">not compared</span>')+'</td>'+
      '<td class="n">'+(r.iso==null?'':(zero?'<span class="st MATCH">0</span>':
        '<span class="bad">'+esc(d)+'</span>'))+'</td>'+
      '<td class="'+(CLS[r.status]||'')+'">'+esc(r.status||'')+'</td>'+
      '<td class="det">'+esc((r.detail||r.first_differences||'').slice(0,150))+
      '</td></tr>';
  });
  $('rows').innerHTML=h;
}
function summarise(s){
  if(!s) return;
  let m=[];
  if(s.compared){
    m.push('<b>'+s.agree+' of '+s.rated+'</b> match ISO on the premium and '+
      'every published field');
    const bad=s.differ.length+s.premium_only.length;
    if(bad) m.push('<span class="bad">'+bad+' with a difference ('+
      esc(s.differ.concat(s.premium_only).join(', '))+')</span>');
  } else {
    m.push('<b>'+s.rated+' of '+s.total+'</b> rated by our engine — '+
      '<span class="am">not compared against ISO</span>');
  }
  if(s.engine_stopped.length) m.push('<span class="bad">'+
    s.engine_stopped.length+' refused by our engine ('+
    esc(s.engine_stopped.join(', '))+')</span>');
  if(s.not_applicable.length) m.push(s.not_applicable.length+
    ' cannot express it (grey — not a failure)');
  if(s.live_calls) m.push(s.live_calls+' live calls');
  let foot='';
  if(s.unmoved.length) foot='<div class="hint">Note: the premium is '+
    'identical to the unvaried base in '+s.unmoved.length+' state(s) ('+
    esc(s.unmoved.join(', '))+'), so agreement there is agreement on a number '+
    'the configuration never changed.</div>';
  $('summary').innerHTML=esc(s.describes||'the base risk, unvaried')+
    '<br>'+m.join(' · ')+' · '+s.seconds+'s'+foot;
}

function check(){
  $('summary').textContent='checking the declaration in all 51...';
  post('/api/tester/legality',{config:CONFIG}).then(j=>{
    const no=Object.entries(j.not_applicable);
    let h='<b>'+j.summary+'</b> jurisdictions can express '+
      esc(j.describes)+'.';
    if(no.length){
      h+='<div class="scroll" style="margin-top:8px"><table>'+
        '<tr><th>State</th><th>Why not</th></tr>'+
        no.map(([k,v])=>'<tr><td>'+esc(k)+'</td><td class="det">'+
          esc(v)+'</td></tr>').join('')+'</table></div>';
    }
    $('summary').innerHTML=h;
  });
}

// ---- the long view
const VIEWS=[['qa','QA summary'],['review','What the review found'],
  ['history','Agreement over time'],['coverage','Coverage'],
  ['curve','Premium response'],['defects','Defects']];
let CURRENT='qa';
function tabs(){
  $('views').innerHTML=VIEWS.map(([v,l])=>'<button data-v="'+v+'"'+
    (v===CURRENT?' class="on"':'')+'>'+l+'</button>').join('');
  document.querySelectorAll('#views button').forEach(b=>b.onclick=()=>{
    CURRENT=b.dataset.v; tabs(); loadView(CURRENT); });
}
function loadView(v){
  const box=$('view'); box.innerHTML='<span class="hint">loading...</span>';
  if(v==='qa') return fetch('/api/tester/qa/summary').then(r=>r.json())
    .then(j=>{
      const c=j.counts, comparable=c.agrees+c.differs;
      box.innerHTML=j.verdict
        +'<div class="hint" style="margin:6px 0 2px">Across <b>'+j.runs+'</b> QA run(s), '
        +'<b>'+j.scenarios+'</b> scenario(s), <b>'+j.live_calls+'</b> ISO call(s). '
        +(comparable?'':'<b>Nothing compared against ISO yet</b> — these were offline runs, '
          +'so there is nothing to agree with. ')
        +'</div>'
        +j.map
        +'<div class="hint"><b>The map is a tile grid, not a projection.</b> Every '
        +'jurisdiction gets the same square: Rhode Island and Texas carry one submission '
        +'each, and drawing Texas 200 times larger would say something untrue about where '
        +'the testing went. <b>Hawaii is drawn and permanently blank</b> — it is not in '
        +'ISO’s corpus at all, and leaving it off would hide that.</div>';
    });
  if(v==='review') return fetch('/api/tester/qa/review').then(r=>r.json())
    .then(j=>{
      const p3=j.pass3, c=p3.counts;
      let h='<div class="hint" style="margin-bottom:8px">The harness checking '
        +'its own results. <b>Two different things are on this page</b>: what it '
        +'has already settled, and what still needs a human.</div>';

      h+='<h3 style="margin:10px 0 4px;font-size:14px">1. Settled &mdash; every '
        +'&ldquo;not offered here&rdquo; was checked against ISO&rsquo;s own files</h3>';
      h+='<div class="hint">A jurisdiction reporting <b>not applicable</b> is the '
        +'one outcome never counted as a failure, so it is the one place a '
        +'mistake can hide. Each was re-derived from ISO&rsquo;s files using '
        +'different code.</div>';
      h+='<table style="margin:6px 0"><tr><th>Verdict</th><th class="n">Count</th>'
        +'<th>Means</th></tr>'
        +'<tr><td><b>Confirmed</b></td><td class="n">'+c.CONFIRMED+'</td>'
        +'<td>ISO&rsquo;s files agree &mdash; genuinely not offered there</td></tr>'
        +'<tr><td style="color:var(--red)"><b>Contradicted</b></td><td class="n">'
        +p3.contradicted.length+'</td><td><b>ISO does offer it. The refusal is '
        +'ours</b> &mdash; this is a defect</td></tr>'
        +'<tr><td>Unverified</td><td class="n">'+c.UNVERIFIED+'</td>'
        +'<td>Could not be settled from the files, and says so</td></tr></table>';
      if(p3.contradicted.length){
        h+='<div class="hint" style="color:var(--red)"><b>Findings:</b></div><ul>'
          +p3.contradicted.map(x=>'<li><b>'+esc(x.juris)+'</b> &middot; '
          +esc(x.describes)+'<br><span style="color:var(--muted)">'+esc(x.why)
          +'</span></li>').join('')+'</ul>';
      } else {
        h+='<div class="hint"><b>No findings.</b> Every refusal on record is '
          +'ISO&rsquo;s narrowing, not ours.</div>';
      }
      if(p3.causes && p3.causes.length){
        h+='<div class="hint" style="margin-top:6px">Why jurisdictions could not '
          +'express a configuration:</div><ul>'
          +p3.causes.map(g=>'<li>'+esc(g.why)+' <span style="color:var(--muted)">'
          +'&mdash; '+g.n+' time(s): '+esc(g.states.join(' '))+'</span></li>')
          .join('')+'</ul>';
      }

      h+='<h3 style="margin:16px 0 4px;font-size:14px">2. Needs a person &mdash; '
        +'claims worth attacking</h3>';
      h+='<div class="hint">Each of these is a claim <b>we</b> are making. The '
        +'review asks three specialists to <b>disprove</b> it, each reading a '
        +'different source. <b>They are dispatched by hand, not from this page</b> '
        +'&mdash; so nothing here says a review has happened.</div>';
      if(!j.briefs.length){
        h+='<div class="hint">Nothing to attack. A clean agreement is not a '
          +'claim &mdash; there is nothing to disprove.</div>';
      } else {
        h+='<ul>'+j.briefs.map(g=>'<li><b>'+esc(g.claim)+'</b><br>'
          +'<span style="color:var(--muted)">'+g.n+' scenario(s) &middot; '
          +esc(g.states.join(' '))+'<br>Ask: '+esc(g.question||'')+'<br>'
          +'Reviewers: '+esc(g.reviewers.join(', '))+'</span></li>').join('')
          +'</ul>';
      }

      h+='<h3 style="margin:16px 0 4px;font-size:14px">3. The calls we did not '
        +'make</h3>';
      if(!j.payloads.length){
        h+='<div class="hint">None exported yet. Run '
          +'<code>python scripts/qa_review.py --payloads</code>.</div>';
      } else {
        h+='<div class="hint">When our engine refuses, ISO never sees the '
          +'submission &mdash; so <b>&ldquo;ISO would refuse it too&rdquo; is a '
          +'guess.</b> These are those submissions, ready to send by hand. '
          +'<b>'+j.payloads.length+'</b> in <code>'+esc(j.payload_dir)+'</code>'
          +'</div><div class="hint">'+j.payloads.slice(0,24).map(esc).join(' &middot; ')
          +(j.payloads.length>24?' &hellip;':'')+'</div>';
      }
      box.innerHTML=h;
    });
  if(v==='history') return fetch('/api/tester/history').then(r=>r.json())
    .then(j=>{ box.innerHTML=j.chart+
      '<div class="hint">'+j.runs.length+' stored run(s). Only ISO-compared '+
      'runs are charted — an engine-only run has nothing to agree with.</div>'+
      '<div class="scroll"><table><tr><th>When</th><th>Configuration</th>'+
      '<th>Agree</th><th>Rated</th><th>N/A</th></tr>'+
      j.series.slice().reverse().map(s=>'<tr><td>'+esc(s.at_iso)+'</td><td>'+
        esc(s.describes)+'</td><td class="n">'+(s.compared?s.agree:'—')+
        '</td><td class="n">'+s.rated+'</td><td class="n">'+
        s.not_applicable+'</td></tr>').join('')+'</table></div>'; });
  if(v==='coverage') return fetch('/api/tester/coverage').then(r=>r.json())
    .then(j=>{ box.innerHTML='<div class="hint">'+j.exercised+' of '+j.controls+
      ' controls have ever been exercised. Filled = rated there at least once; '+
      'hollow = asked and not declarable there; empty = never run.</div>'+
      j.chart; });
  if(v==='curve'){
    const opts=SPEC.controls.map(c=>'<option value="'+c.id+'">'+esc(c.label)+
      '</option>').join('');
    box.innerHTML='<label>Control</label><select id="cv" style="max-width:280px">'+
      opts+'</select><div id="cvout"></div>';
    const draw=()=>fetch('/api/tester/curve/'+$('cv').value).then(r=>r.json())
      .then(j=>{ $('cvout').innerHTML=j.chart+'<div class="hint">'+
        j.jurisdictions+' jurisdiction(s) have two or more stored values for '+
        esc(j.label)+' and can be drawn; '+j.with_any_value+' have at least '+
        'one. Values run so far: '+(j.values_seen.map(esc).join(', ')||'none')+
        '. Only runs that varied this control ALONE are drawn — a curve '+
        'mixing configurations is not a curve.</div>'; });
    $('cv').onchange=draw; return draw();
  }
  if(v==='defects') return fetch('/api/tester/defects').then(r=>r.json())
    .then(j=>{ box.innerHTML=j.defects.length?
      '<div class="scroll"><table><tr><th>State</th><th>Outcome</th>'+
      '<th>Configuration</th><th>First seen</th><th>Last seen</th>'+
      '<th>Runs</th><th>Detail</th></tr>'+j.defects.map(d=>'<tr><td>'+
      esc(d.juris)+'</td><td class="bad">'+esc(d.status)+'</td><td>'+
      esc(d.describes)+'</td><td class="det">'+esc(d.first_seen)+
      '</td><td class="det">'+esc(d.last_seen)+'</td><td class="n">'+d.runs+
      '</td><td class="det">'+esc(d.detail)+'</td></tr>').join('')+'</table></div>'
      :'<div class="hint">No refusal or disagreement recorded yet.</div>'; });
}

function post(url,body){
  return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)}).then(r=>r.json()).then(j=>{
      if(j.error) throw j.error; return j; });
}
$('qarun').onclick=qaRun;
$('qaplan').onclick=qaPlan;
$('qalive').onchange=()=>{QAARMED=false;
  $('qarun').textContent='Start';$('qarun').style.background='';
  qaBudget();};
qaLoad();
$('run').onclick=run; $('check').onclick=check;
$('compare').onchange=cost;
$('reset').onclick=()=>{ CONFIG={}; panel(); cost();
  note('Cleared. With nothing set, a run rates the unvaried base risk.'); };

fetch('/api/tester/spec').then(r=>r.json()).then(j=>{
  SPEC=j;
  $('sub').textContent=SPEC.controls.length+' controls · '+
    SPEC.jurisdictions.length+' jurisdictions · options as filed for '+
    SPEC.asof+' (built in '+SPEC.built_in_seconds+'s)';
  panel(); cost(); tabs(); loadView(CURRENT);
});
</script></body></html>"""
