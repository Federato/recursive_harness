"""The review page: one run's findings, a pattern match where one exists, a
brief where one doesn't, and a place to paste back what a person said.

    /review/<run-file>                    the page
    /api/review/<run-file>/spec           findings + status, GET
    /api/review/<run-file>/brief          {key} -> {brief_md}, POST
    /api/review/<run-file>/post           {key, text} -> {ok}, POST
    /api/review/<run-file>/clear          {key} -> {ok}, POST

**The run file itself is never touched.** It is a static, self-contained
artifact that opens with no server running -- a promise made more than once in
this project's own docs -- so review lives entirely in a second page and a
second store (`results/reviews/`), keyed to the run file's name. The run file
gains exactly one outbound link to get here.

**No API key reaches this file, or any file it imports.** `reviews.py` does the
only two things that don't need one: a mechanical pattern match, and a brief
for a person to paste into a conversation they're already having. What comes
back is pasted in by hand.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import reviews                                                # noqa: E402

from . import runfile                                         # noqa: E402


def _entry_for(run_file: str) -> dict | None:
    for e in runfile.entries():
        if e.get("file") == run_file:
            return e
    return None


def _spec(run_file: str) -> tuple:
    entry = _entry_for(run_file)
    if entry is None:
        return 404, json.dumps({"error": "no such run file"}), "json"
    run_ids = entry.get("run_ids") or []
    findings = reviews.build_findings(run_file, run_ids)
    return 200, json.dumps({
        "run_file": run_file, "layer": entry.get("layer"), "name": entry.get("name"),
        "class_code": entry.get("class_code"), "rated": entry.get("rated", 0),
        "status": reviews.status(findings),
        "findings": findings,
    }), "json"


def _brief(run_file: str, body: dict) -> tuple:
    entry = _entry_for(run_file)
    if entry is None:
        return 404, json.dumps({"error": "no such run file"}), "json"
    key = (body or {}).get("key") or ""
    md = reviews.generate_brief(run_file, entry.get("run_ids") or [], key)
    if md is None:
        return 404, json.dumps({"error": "no such finding"}), "json"
    return 200, json.dumps({"brief_md": md}), "json"


def _post(run_file: str, body: dict) -> tuple:
    entry = _entry_for(run_file)
    if entry is None:
        return 404, json.dumps({"error": "no such run file"}), "json"
    key = (body or {}).get("key") or ""
    text = (body or {}).get("text") or ""
    if not text.strip():
        return 400, json.dumps({"error": "nothing to post"}), "json"
    ok = reviews.post_analysis(run_file, entry.get("run_ids") or [], key, text)
    if not ok:
        return 404, json.dumps({"error": "no such finding"}), "json"
    return 200, json.dumps({"ok": True}), "json"


def _clear(run_file: str, body: dict) -> tuple:
    key = (body or {}).get("key") or ""
    ok = reviews.clear_analysis(run_file, key)
    return (200, json.dumps({"ok": ok}), "json") if ok else \
           (404, json.dumps({"error": "no such finding"}), "json")


def dispatch(method: str, path: str, query: dict, body):
    """Handle a `/review` route, or return None so the caller keeps looking."""
    if path.startswith("/review/") and method == "GET":
        run_file = path[len("/review/"):]
        if not run_file or ".." in run_file or "/" in run_file:
            return 404, json.dumps({"error": "no such run file"}), "json"
        if _entry_for(run_file) is None:
            return 404, json.dumps({"error": "no such run file"}), "json"
        return 200, PAGE.replace("__RUN_FILE__", json.dumps(run_file)), "html"
    if not path.startswith("/api/review/"):
        return None
    rest = path[len("/api/review/"):]
    if "/" not in rest:
        return 404, json.dumps({"error": "not found"}), "json"
    run_file, action = rest.rsplit("/", 1)
    if method == "GET" and action == "spec":
        return _spec(run_file)
    if method == "POST" and action == "brief":
        return _brief(run_file, body or {})
    if method == "POST" and action == "post":
        return _post(run_file, body or {})
    if method == "POST" and action == "clear":
        return _clear(run_file, body or {})
    return 404, json.dumps({"error": "not found"}), "json"


PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>Review -- GL rating engine</title>
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
nav{margin-left:auto}
nav a{font-size:13px;text-decoration:none;color:var(--blue);padding:5px 10px;
border:1px solid var(--line);border-radius:6px;background:#fff}
main{padding:16px 20px;max-width:820px}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;
padding:14px 16px;margin-bottom:16px}
.card h2{font-size:12px;text-transform:uppercase;letter-spacing:.05em;
color:var(--muted);margin:0 0 11px;font-weight:650}
button{background:var(--blue);color:#fff;border:0;border-radius:6px;
padding:8px 13px;font-size:13px;font-weight:600;cursor:pointer}
button.ghost{background:#fff;color:var(--ink);border:1px solid #cbd2d9;font-weight:500}
button:disabled{opacity:.5;cursor:default}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}
.note{font-size:11.5px;color:var(--muted);border-left:2px solid var(--line);
padding-left:8px;margin-top:9px}
.warn{font-size:11.5px;color:var(--amber);border-left:2px solid var(--amber);
padding-left:8px;margin-top:9px}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;
background:#eef2f6;color:var(--muted);margin-right:5px}
.tag.match{background:#eaf2fa;color:var(--blue)}
.tag.local{background:#faf1e2;color:var(--amber)}
.tag.nomatch{background:#faf1e2;color:var(--amber)}
.brief{background:#0f1216;color:#d8dde3;border-radius:7px;padding:14px 16px;
font-family:ui-monospace,"SF Mono",Consolas,monospace;font-size:12px;
line-height:1.55;overflow-x:auto;white-space:pre-wrap;margin-top:10px}
textarea{width:100%;min-height:110px;padding:9px 10px;border:1px solid #cbd2d9;
border-radius:6px;font-size:12.5px;font-family:inherit;resize:vertical}
.posted{border:1px solid var(--line);border-radius:7px;padding:12px 14px;
background:#fbfcfd;margin-top:8px;white-space:pre-wrap}
.posted .meta{font-size:11px;color:var(--muted);margin-bottom:8px}
.finding{border:1px solid var(--line);border-radius:7px;padding:12px 14px;
margin-bottom:12px}
.finding h3{margin:0 0 5px;font-size:13px}
.finding .st{font-weight:650;font-size:11.5px}
.finding .st.DIFF,.finding .st.PREMIUM{color:var(--red)}
.finding .st.ENGINE,.finding .st.BUILD,.finding .st.RAAS{color:var(--red)}
.det{color:var(--muted);font-size:11.5px}
.big{font-size:15px;font-weight:650;margin:2px 0 6px}
.dot{display:inline-block;width:9px;height:9px;border-radius:99px;margin-right:7px;
vertical-align:middle}
.dot.clean{background:var(--blue)} .dot.needs{background:var(--red)}
.dot.explained{background:var(--amber)} .dot.reviewed{background:var(--blue)}
.err{color:var(--red);font-size:12px}
</style></head><body>
<header>
  <h1>Review</h1>
  <div class="sub" id="subhead">loading&hellip;</div>
  <nav><a href="/tests">&larr; Back to Tests</a></nav>
</header>
<main id="main"><div class="card"><div class="det">loading&hellip;</div></div></main>
<script>
const $ = s => document.querySelector(s);
const RUN_FILE = __RUN_FILE__;
async function get(u){ const r = await fetch(u); return r.json(); }
async function post(u,b){ const r = await fetch(u,{method:'POST',
  headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)});
  return r.json(); }

function statusLine(status, n){
  const map = {clean: ['clean', 'Everything passed'],
    needs_review: ['needs', n + ' finding(s) need a look'],
    explained: ['explained', n + ' finding(s), all accounted for'],
    reviewed: ['reviewed', n + ' finding(s), all reviewed by a person']};
  const [cls, label] = map[status] || ['needs', status];
  return `<span class="dot ${cls}"></span>${label}`;
}

function patternTag(p){
  if(!p) return '<span class="tag nomatch">no known pattern</span>';
  const cls = p.kind === 'iso_question' ? 'match' : 'local';
  return `<span class="tag ${cls}">${esc(p.label)}</span>`;
}

function esc(s){ const d = document.createElement('div'); d.textContent = s||''; return d.innerHTML; }

async function draw(){
  const spec = await get(`/api/review/${RUN_FILE}/spec`);
  if(spec.error){ $('#main').innerHTML = `<div class="card"><span class="err">${esc(spec.error)}</span></div>`; return; }
  $('#subhead').textContent = `${spec.layer} ${spec.name}${spec.class_code ? ' · class ' + spec.class_code : ''} · ${RUN_FILE}`;
  const findings = Object.values(spec.findings);

  let h = `<div class="card"><p class="big">${statusLine(spec.status, findings.length)}</p>`;
  if(!findings.length){
    h += `<div class="note">Computed straight from the run's own rows -- no
      brief, no pattern match, nothing written to a review record. A clean
      run has nothing to say beyond the number that already says it.</div>`;
  }
  h += `</div>`;

  for(const f of findings){
    h += `<div class="card finding" data-key="${esc(f.key)}">`
       + `<h3><span class="st ${f.status.split(' ')[0]}">${esc(f.status)}</span> &middot; ${esc(f.juris)}</h3>`
       + `<div class="det">${esc(f.config)}</div>`;
    if(f.status === 'DIFF' || f.status === 'PREMIUM ONLY')
      h += `<div class="det" style="margin-top:4px">ours=${esc(f.ours)} &middot; iso=${esc(f.iso)} &middot; delta=${esc(f.delta)}</div>`;
    else
      h += `<div class="det" style="margin-top:4px">${esc(f.detail)}</div>`;
    h += `<div class="row">${patternTag(f.pattern)}</div>`;

    if(f.pattern && f.pattern.kind === 'seen_before')
      h += `<div class="posted"><div class="meta">from ${esc(f.pattern.run_file)}</div>${esc(f.pattern.prior_analysis)}</div>`;

    if(f.analysis){
      h += `<div class="posted"><div class="meta">Posted ${esc((f.analysis_posted_at||'').replace('T',' '))} &middot; pasted, not verified</div>${esc(f.analysis)}</div>`
         + `<div class="row"><button class="ghost" onclick="clearAnalysis('${esc(f.key)}')">Clear posted analysis</button></div>`;
    } else if(!f.pattern) {
      if(f.brief_md){
        h += `<div class="brief">${esc(f.brief_md)}</div>`
           + `<div class="row"><button class="ghost" onclick="copyBrief('${esc(f.key)}')">Copy</button></div>`
           + `<div class="warn">This holds ISO's licensed values, same as a run file. Pasting it into a chat you control is the intended use.</div>`
           + `<div class="row" style="margin-top:12px"><textarea id="ta-${esc(f.key)}" placeholder="Paste what came back here"></textarea></div>`
           + `<div class="row"><button onclick="postAnalysis('${esc(f.key)}')">Post to this finding</button></div>`
           + `<div class="note">Stored as free text, verbatim -- not re-parsed, not treated as a verdict.</div>`;
      } else {
        h += `<div class="row"><button onclick="genBrief('${esc(f.key)}')">Generate a review brief</button></div>`;
      }
    }
    h += `</div>`;
  }
  $('#main').innerHTML = h;
  window._briefs = {};
  findings.forEach(f => { if(f.brief_md) window._briefs[f.key] = f.brief_md; });
}

async function genBrief(key){
  await post(`/api/review/${RUN_FILE}/brief`, {key});
  draw();
}
async function postAnalysis(key){
  const ta = document.getElementById('ta-' + key);
  if(!ta || !ta.value.trim()) return;
  await post(`/api/review/${RUN_FILE}/post`, {key, text: ta.value});
  draw();
}
async function clearAnalysis(key){
  await post(`/api/review/${RUN_FILE}/clear`, {key});
  draw();
}
function copyBrief(key){
  const text = (window._briefs || {})[key] || '';
  navigator.clipboard.writeText(text);
}

draw();
</script>
</body></html>
"""
