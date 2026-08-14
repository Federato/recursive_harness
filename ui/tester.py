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

from . import charts, store, variables                        # noqa: E402

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
    """Handle a tester route, or return None so the caller keeps looking."""
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
</style></head><body>
<header>
  <h1>Variable tester</h1>
  <span class="sub" id="sub">loading ISO's declared options...</span>
  <nav><a href="/">Rate one submission</a><a href="/tester" class="on">Variable tester</a></nav>
</header>
<main>
 <div>
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
const VIEWS=[['history','Agreement over time'],['coverage','Coverage'],
  ['curve','Premium response'],['defects','Defects']];
let CURRENT='coverage';
function tabs(){
  $('views').innerHTML=VIEWS.map(([v,l])=>'<button data-v="'+v+'"'+
    (v===CURRENT?' class="on"':'')+'>'+l+'</button>').join('');
  document.querySelectorAll('#views button').forEach(b=>b.onclick=()=>{
    CURRENT=b.dataset.v; tabs(); loadView(CURRENT); });
}
function loadView(v){
  const box=$('view'); box.innerHTML='<span class="hint">loading...</span>';
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
