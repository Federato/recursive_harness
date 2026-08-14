"""Stage 6 -- the interface. Paste a submission, rate it, read the result.

Run it:

    python app.py            # then open http://127.0.0.1:8765

**Strictly separate from the engine.** This file imports `gl_engine`; nothing in
`gl_engine` imports this, and the engine has no idea it exists. That separation
was the whole point of the stage: the plan wrote, before any of it was built,
*"we expect it to prove the separation rather than build anything -- if the UI
needs the engine to change, the engine's interface was wrong."*

Everything below is assembled from the public surface of a `Rating`:
`premium`, `by_coverage`, `referrals`, `messages`, `trace`, `tree`, `packages`.
**No engine change was needed to build it**, which is the result the stage was
there to test. The same call works in a notebook:

    from gl_engine.rating import Kernel
    Kernel().rate("Engine_Payloads/OK/submission.json").premium

Standard library only -- no framework, no build step, one file.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import uuid
import webbrowser
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from gl_engine import EditionResolver                       # noqa: E402
from gl_engine.interp import tree                           # noqa: E402
from gl_engine.rating import Kernel, MODES, STRICT          # noqa: E402
from gl_engine.schema import Schema, validate               # noqa: E402
from gl_engine.resolve import ResolvedBook                  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
try:
    from raas import NO_ISO, RaaS, RaaSError                # noqa: E402
except Exception:                                           # noqa: BLE001
    RaaS = None                                             # ISO comparison off
    NO_ISO = frozenset()

    class RaaSError(RuntimeError):
        pass

SAMPLES = ROOT / "Engine_Payloads"
HOST, PORT = "127.0.0.1", 8765

#: Built once. Discovery is ~1s and every rating would otherwise pay it.
RESOLVER = EditionResolver()
KERNELS = {m: Kernel(mode=m, resolver=RESOLVER) for m in MODES}

#: `NO_ISO` -- jurisdictions the subscription does not cover -- is defined in
#: `scripts/raas.py`, next to the client that hits the boundary. They still rate
#: offline and still appear in an engine-only run; they are left out only of a
#: comparison, where there is nothing to compare against.

#: One shared RAaS client. Authenticating per request would spend a token
#: handshake on every rating; the client refreshes its own token when it
#: expires.
_ISO_LOCK = threading.Lock()
_ISO = {"client": None, "error": None}


def iso_client():
    """The live ISO client, or None with the reason recorded.

    **Never raises.** ISO being unreachable must degrade the page to
    engine-only, not break rating -- the engine is the product and the
    comparison is the check.
    """
    with _ISO_LOCK:
        if _ISO["client"] is None and _ISO["error"] is None:
            if RaaS is None:
                _ISO["error"] = "scripts/raas.py not importable"
            else:
                try:
                    _ISO["client"] = RaaS()
                except Exception as exc:                    # noqa: BLE001
                    _ISO["error"] = str(exc)[:200]
        return _ISO["client"]


def compare_with_iso(payload: dict, ours) -> dict:
    """Rate the same submission through ISO and say whether they agree.

    The verdict is on the premium, because that is what a reader wants first;
    the field-level difference is reported alongside it so a total that is
    right for the wrong reasons is still visible.
    """
    # Ask first whether ISO can be asked at all. Sending a submission we know
    # will be refused spends a call to produce a 401 that reads like a fault.
    juris = ((payload.get("body", {}).get("SchemeKeys", {})
              .get("ProductName") or "").split() or [""])[-1]
    if juris in NO_ISO:
        return {"available": False,
                "reason": f"{juris} is not on the ISO subscription, so there "
                          f"is no external answer to compare against"}
    client = iso_client()
    if client is None:
        return {"available": False, "reason": _ISO["error"] or "not configured"}
    try:
        live = client.rate(payload)
    except Exception as exc:                                # noqa: BLE001
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"[:200]}

    body = live.get("Body", {})
    gl = (body.get("GeneralLiability") or [{}])[0]
    iso_premium = gl.get("Premium")
    scheme = live.get("Header", {}).get("Scheme", "")
    parts = scheme.split()
    iso_pkg = f"GL_{parts[1]}_{parts[2]}_{parts[3]}" if len(parts) >= 4 else ""
    agrees = (iso_premium is not None
              and Decimal(str(iso_premium)) == ours.premium)
    return {
        "available": True,
        "premium": str(iso_premium) if iso_premium is not None else None,
        "agrees": agrees,
        "delta": str(ours.premium - Decimal(str(iso_premium)))
                 if iso_premium is not None else "",
        "package": iso_pkg,
        "edition_agrees": iso_pkg == ours.packages[0] if iso_pkg else None,
        "messages": body.get("RatingMessages", {}) or {},
    }


#: Batch jobs, keyed by id. A batch of 51 makes 51 live calls at roughly ten
#: seconds each, so it runs in a thread and the page polls -- a request that
#: takes nine minutes to answer is a request that times out.
JOBS: dict = {}
JOBS_LOCK = threading.Lock()


def _batch_worker(job_id: str, jurisdictions: list, mode: str, rounding: str,
                  compare: bool) -> None:
    kernel = KERNELS[mode] if rounding == "ROUND_HALF_UP" else Kernel(
        mode=mode, rounding=rounding, resolver=RESOLVER)
    for i, juris in enumerate(jurisdictions, start=1):
        src = SAMPLES / juris / "submission.json"
        row = {"n": i, "juris": juris}
        try:
            payload = json.loads(src.read_text(encoding="utf-8"))
            r = kernel.rate(payload)
            if not r.complete:
                row.update(status="ENGINE STOPPED",
                           detail=str(r.stopped)[:140])
            else:
                row.update(engine=str(r.premium),
                           packages=" over ".join(r.packages),
                           referrals=len(r.referrals))
                if compare:
                    c = compare_with_iso(payload, r)
                    if not c["available"]:
                        row.update(status="ISO UNAVAILABLE",
                                   detail=c["reason"])
                    else:
                        row.update(iso=c["premium"], delta=c["delta"],
                                   status="PASS" if c["agrees"] else "FAIL")
                else:
                    row.update(status="RATED")
        except Exception as exc:                            # noqa: BLE001
            row.update(status="ERROR", detail=f"{type(exc).__name__}: {exc}"[:140])
        with JOBS_LOCK:
            JOBS[job_id]["rows"].append(row)
            JOBS[job_id]["done"] = i
    with JOBS_LOCK:
        JOBS[job_id]["finished"] = True
        JOBS[job_id]["ended"] = time.time()


#: Trace kinds that are a rating FACTOR -- a number that entered the premium
#: and can be pointed at. The rest of the trace is control flow.
FACTOR_KINDS = ("lookup", "lookup-banded", "lookup-interpolated", "round")


def _subline_premiums(rating) -> list:
    """Premium per subline, from the stat code ISO writes on each coverage.

    `Subline` is `334` for premises/operations and `336` for products, and it
    is written by `ErcSetStatisticalCodes` -- which was silently skipped until
    the `ancestor::` axis was implemented, because asking this very question is
    what exposed it.
    """
    out: dict[str, dict] = {}
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability",
                            rating.tree):
        for loc in tree.select("GeneralLiabilityLocationTable/"
                               "GeneralLiabilityLocation", risk):
            for cls in tree.select("GeneralLiabilityClassificationTable/"
                                   "GeneralLiabilityClassification", loc):
                for cov in cls.children:
                    if not cov.children:
                        continue
                    sub = tree.read("Subline", cov)
                    prem = tree.read("Premium", cov)
                    if not sub or prem in (None, "", "0"):
                        continue
                    e = out.setdefault(sub, {"subline": sub, "premium": Decimal(0),
                                             "coverages": []})
                    e["premium"] += Decimal(prem)
                    e["coverages"].append({"coverage": cov.tag,
                                           "premium": str(Decimal(prem))})
    return [{**v, "premium": str(v["premium"])}
            for v in sorted(out.values(), key=lambda x: x["subline"])]


#: Written onto a coverage but not part of the price -- statistical reporting
#: codes and the subline they belong to.
def _is_stat(tag: str) -> bool:
    return tag.endswith("StatCode") or tag == "Subline"


#: The named milestones in a coverage's chain, so the eye can follow it.
MILESTONES = ("BaseRate", "FinalILF", "FinalRate", "BasicLimitPremium",
              "MedicalPaymentsCharge", "MinPremium", "Premium")


def _chain(cov) -> dict:
    """One coverage's rating chain, in the order the engine computed it.

    **Tree order is computation order** -- a node is appended when a rule
    writes it -- so the chain reads as the narrative it actually was:
    loss cost, LCM, base rate, ILF, deductible, size of risk, basic limit
    premium, final rate, premium.

    Zero-valued steps are omitted from `factors` and **named in `omitted`**
    rather than dropped silently. That distinction matters here more than
    most places: this corpus has eight meanings of zero, and a zero where a
    rate belonged is the defect this whole engine exists to refuse. A
    simplified view may not be the thing that hides one.
    """
    factors, omitted = [], []
    for ch in cov.children:
        if ch.children or _is_stat(ch.tag) or ch.text in (None, ""):
            continue
        try:
            v = Decimal(ch.text)
        except Exception:                                   # noqa: BLE001
            continue
        if v == 0:
            omitted.append(ch.tag)
            continue
        factors.append({"factor": ch.tag, "value": str(v),
                        **({"milestone": True} if ch.tag in MILESTONES else {})})
    prem = tree.read("Premium", cov)
    return {"coverage": cov.tag, "premium": prem,
            "subline": tree.read("Subline", cov),
            "factors": factors,
            "omitted_zero": omitted}


def _rating(rating) -> dict:
    """The simplified view: what actually rated, and what it came to."""
    covs = []
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability",
                            rating.tree):
        for loc in tree.select("GeneralLiabilityLocationTable/"
                               "GeneralLiabilityLocation", risk):
            for cls in tree.select("GeneralLiabilityClassificationTable/"
                                   "GeneralLiabilityClassification", loc):
                for cov in cls.children:
                    if not cov.children:
                        continue
                    prem = tree.read("Premium", cov)
                    if prem in (None, "", "0"):
                        continue
                    c = _chain(cov)
                    c["class_code"] = tree.read("ClassCode", cls)
                    covs.append(c)
    return {"coverages": covs, "premium": str(rating.premium)}


def _factors(rating) -> list:
    """Every rating factor, in the order it was used, as structured data.

    The trace carries `data` for exactly this: a factor is a table, a set of
    keys, a value and the package it came from, and squeezing that into a
    sentence made it unreadable on a screen. `detail` is kept as a one-line
    summary; the parts are what the JSON panel renders.
    """
    out = []
    for i, t in enumerate(rating.trace):
        if t.kind not in FACTOR_KINDS:
            continue
        out.append({"step": len(out) + 1, "kind": t.kind, **t.data,
                    "summary": t.detail})
    return out


def rate(payload: dict, mode: str, rounding: str, compare: bool = False) -> dict:
    kernel = KERNELS[mode] if rounding == "ROUND_HALF_UP" else Kernel(
        mode=mode, rounding=rounding, resolver=RESOLVER)
    r = kernel.rate(payload)

    result = {
        "jurisdiction": r.juris, "asof": r.asof, "mode": r.mode,
        "packages": list(r.packages), "complete": r.complete,
        "rounding": rounding,
    }
    if not r.complete:
        result["stopped"] = str(r.stopped)
        result["trace_len"] = len(r.trace)
        return result

    try:
        book = ResolvedBook(RESOLVER.resolve(r.juris, r.asof))
        findings = validate(payload, Schema.for_book(book))
    except Exception as exc:                                # noqa: BLE001
        findings = []
        result["schema_error"] = str(exc)

    if compare:
        result["iso"] = compare_with_iso(payload, r)

    result.update({
        "premium": str(r.premium),
        "by_coverage": [{"coverage": k, "premium": str(v)}
                        for k, v in sorted(r.by_coverage.items(),
                                           key=lambda x: -x[1])],
        "by_subline": _subline_premiums(r),
        "rating": _rating(r),
        "factors": _factors(r),
        "factor_count": len(_factors(r)),
        "referrals": [{"code": x.code, "condition": x.condition,
                       "clears_with": x.needs or "", "where": x.where}
                      for x in r.referrals],
        "messages": r.messages,
        "findings": [{"level": f.level, "code": f.code, "where": f.where,
                      "detail": f.detail} for f in findings],
        "trace_len": len(r.trace),
    })
    return result


PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>GL Rating Engine</title><style>
*{box-sizing:border-box}body{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
margin:0;background:#f6f7f9;color:#1a1d21}
header{background:#1f2933;color:#fff;padding:14px 22px;display:flex;
align-items:baseline;gap:16px;flex-wrap:wrap}
header h1{margin:0;font-size:17px;font-weight:600}
header span{opacity:.7;font-size:13px}
.wrap{display:flex;gap:18px;padding:18px;align-items:flex-start;
max-width:1600px;margin:0 auto}
.col{flex:1 1 0;min-width:0}
.card{background:#fff;border:1px solid #dde1e6;border-radius:6px;margin-bottom:14px;
overflow:hidden}
.card h2{margin:0;padding:9px 14px;font-size:13px;font-weight:600;
background:#eef1f4;border-bottom:1px solid #dde1e6;border-radius:6px 6px 0 0}
.card .body{padding:12px 14px}
textarea{width:100%;height:190px;font:12px/1.45 ui-monospace,Consolas,monospace;
border:1px solid #cbd2d9;border-radius:4px;padding:9px}
select,button{font:14px inherit;padding:7px 11px;border:1px solid #cbd2d9;
border-radius:4px;background:#fff}
button{background:#2b6cb0;color:#fff;border-color:#2b6cb0;cursor:pointer;font-weight:600}
button:disabled{opacity:.55;cursor:default}
.row{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
.premium{font-size:30px;font-weight:700}
.muted{color:#66727f;font-size:12px}
table{width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed}
td{overflow-wrap:anywhere}
td,th{padding:5px 7px;border-bottom:1px solid #eef1f4;text-align:left;
vertical-align:top}
th{font-size:11px;text-transform:uppercase;color:#66727f;font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
code{font:12px ui-monospace,Consolas,monospace;background:#f2f4f6;padding:1px 4px;
border-radius:3px;word-break:break-all}
.pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:11px;
font-weight:600}
.refer{background:#fef3c7;color:#92400e}
.err{background:#fee2e2;color:#991b1b}
.warn{background:#fef3c7;color:#92400e}
.info{background:#e0f2fe;color:#075985}
.stopped{background:#fee2e2;border:1px solid #fca5a5;padding:11px;border-radius:4px}
.scroll{max-height:340px;overflow:auto}
pre.json{margin:0;max-width:100%;font:12px/1.5 ui-monospace,Consolas,monospace;background:#1f2933;
color:#d7dde3;padding:12px;border-radius:4px;max-height:560px;overflow:auto;
white-space:pre;tab-size:2}
pre.json .k{color:#8fd0ff}pre.json .s{color:#c3e88d}pre.json .n{color:#f7c66b}
.tabs{display:flex;gap:6px;margin-bottom:9px;flex-wrap:wrap}
.tabs button{background:#fff;color:#1a1d21;border:1px solid #cbd2d9;font-weight:500;
padding:5px 10px;font-size:13px}
.tabs button.on{background:#2b6cb0;color:#fff;border-color:#2b6cb0;font-weight:600}
.copy{float:right;font-size:11px;padding:3px 8px;font-weight:500}
tr.ms td{font-weight:700;background:#f7fafc}
tr.total td{font-weight:700;border-top:2px solid #cbd2d9;background:#eef6ff}
.covhead{font-weight:600;margin:12px 0 4px;font-size:13px}
.covhead:first-child{margin-top:0}
.covhead small{font-weight:400;color:#66727f}
.om{font-size:11px;color:#8a94a0;margin-top:5px}
label.chk{display:inline-flex;align-items:center;gap:6px;font-size:13px;
padding:7px 11px;border:1px solid #cbd2d9;border-radius:4px;background:#fff;
cursor:pointer}
.verdict{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.vs{font-size:13px;color:#66727f}
.badge{display:inline-block;padding:3px 12px;border-radius:12px;font-size:13px;
font-weight:700;letter-spacing:.02em}
.pass{background:#d1fae5;color:#065f46}.fail{background:#fee2e2;color:#991b1b}
.na{background:#e5e7eb;color:#4b5563}
.bar{height:26px;border-radius:4px;overflow:hidden;display:flex;
background:#e5e7eb;margin:10px 0 4px}
.bar span{display:block;height:100%}
.bar .p{background:#34d399}.bar .f{background:#f87171}.bar .u{background:#cbd5e1}
.big{font-size:26px;font-weight:700}
tr.rowfail td{background:#fff5f5}
.legend{font-size:12px;color:#66727f;margin-top:2px}
progress{width:100%;height:14px}
</style></head><body>
<header><h1>GL Rating Engine</h1>
<span>ISO content, executed &mdash; every number carries its source</span>
<a href="/tester" style="margin-left:auto;font-size:13px;text-decoration:none;
color:#2b6cb0;background:#fff;border:1px solid #cbd2d9;border-radius:6px;
padding:5px 10px">Variable tester &rarr;</a></header>
<div class="wrap">
 <div class="col">
  <div class="card"><h2>Submission</h2><div class="body">
   <div class="row">
    <select id="sample"><option value="">Load a sample&hellip;</option></select>
    <select id="mode"></select>
    <select id="rounding">
     <option>ROUND_HALF_UP</option><option>ROUND_HALF_EVEN</option>
     <option>ROUND_DOWN</option></select>
    <label class="chk"><input type="checkbox" id="cmp"> Compare with ISO</label>
    <button id="go">Rate</button>
   </div>
   <textarea id="payload" spellcheck="false"
     placeholder="Paste a RAaS submission, or load a sample"></textarea>
  </div></div>
  <div class="card"><h2>Test every jurisdiction</h2><div class="body">
   <div class="row">
    <label class="chk"><input type="checkbox" id="bcmp" checked>
     Also rate through ISO</label>
    <button id="brun">Run the full test</button>
    <span class="muted" id="bnote"></span>
   </div>
   <div id="bprog" style="display:none"><progress id="bbar"></progress>
    <div class="muted" id="bmsg"></div></div>
  </div></div>
  <div class="card" id="jsoncard" style="display:none"><h2>Result
   <button class="copy" id="copy">Copy</button></h2><div class="body">
   <div class="tabs" id="tabs"></div>
   <pre class="json" id="jsonout"></pre>
  </div></div>
 </div>
 <div class="col"><div id="bout"></div><div id="out"></div></div>
</div>
<script>
const $=s=>document.querySelector(s), out=$('#out');
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
// `?sample=OK&mode=underwriting` preloads, so a view can be linked to.
const Q=new URLSearchParams(location.search);
fetch('/api/samples').then(r=>r.json()).then(d=>{
  d.modes.forEach(m=>$('#mode').add(new Option(m,m)));
  d.jurisdictions.forEach(j=>$('#sample').add(new Option(j,j)));
  if(Q.get('mode')) $('#mode').value=Q.get('mode');
  if(Q.get('rounding')) $('#rounding').value=Q.get('rounding');
  if(Q.has('compare')) $('#cmp').checked=Q.get('compare')!=='0';
  // The batch caption counts what will actually run. Jurisdictions ISO will
  // not answer for are left out of a comparison run rather than reported as
  // permanent failures, and the caption says which and why.
  const all=d.jurisdictions.length, skip=d.no_iso||[];
  const setNote=()=>{
    const cmp=$('#bcmp').checked, n=cmp?all-skip.length:all;
    $('#bnote').textContent=n+' submissions, the same risk in every state.'
      +(cmp?' With ISO this takes several minutes.':'')
      +(cmp&&skip.length?' '+skip.join(', ')+' left out — not on the ISO '
        +'subscription, so there is nothing to compare against.':'');
  };
  $('#bcmp').onchange=setNote; setNote();
  const j=Q.get('sample');
  if(j && d.jurisdictions.includes(j)){
    $('#sample').value=j;
    fetch('/api/sample/'+j).then(r=>r.text()).then(t=>{
      $('#payload').value=t;
      if(Q.has('rate')) $('#go').click();
    });
  }
});
$('#sample').onchange=e=>{ if(!e.target.value) return;
  fetch('/api/sample/'+e.target.value).then(r=>r.text())
    .then(t=>{$('#payload').value=t;}); };
function table(head, rows){ if(!rows.length) return '';
  return '<table><tr>'+head.map(h=>'<th>'+h+'</th>').join('')+'</tr>'+
    rows.join('')+'</table>'; }
function card(title, body){ return body ?
  '<div class="card"><h2>'+title+'</h2><div class="body">'+body+'</div></div>' : ''; }
$('#go').onclick=()=>{
  let p; try{ p=JSON.parse($('#payload').value); }
  catch(e){ out.innerHTML=card('Not JSON','<div class="stopped">'+esc(e)+'</div>'); return; }
  $('#go').disabled=true; out.innerHTML='<div class="muted">Rating&hellip;</div>';
  fetch('/api/rate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({payload:p,mode:$('#mode').value,
      rounding:$('#rounding').value,compare:$('#cmp').checked})})
   .then(r=>r.json()).then(render).catch(e=>{
     out.innerHTML=card('Failed','<div class="stopped">'+esc(e)+'</div>');})
   .finally(()=>{$('#go').disabled=false;});
};
// The result panel. Factors are the reason it exists: a rating factor is a
// table, a set of keys, a value and the package it came from, and a table cell
// cannot show that. JSON can, and it can be copied straight into a ticket.
let LAST={}, VIEW='rating';
const VIEWS=[['rating','Rating'],['factors','All steps'],['premiums','Premiums'],
              ['referrals','Referrals'],['all','Everything']];
function slice(d,v){
  if(v==='rating') return d.rating;
  if(v==='factors') return {factors:d.factors};
  if(v==='premiums') return {premium:d.premium, by_subline:d.by_subline,
    by_coverage:d.by_coverage, jurisdiction:d.jurisdiction, asof:d.asof,
    packages:d.packages, rounding:d.rounding, mode:d.mode};
  if(v==='referrals') return {referrals:d.referrals, messages:d.messages,
    findings:d.findings};
  return d;
}
function colour(j){
  return esc(j)
    .replace(/&quot;([^&]*?)&quot;(\s*:)/g,'<span class="k">&quot;$1&quot;</span>$2')
    .replace(/:\s*&quot;([^&]*?)&quot;/g,': <span class="s">&quot;$1&quot;</span>')
    .replace(/:\s*(-?\d+(?:\.\d+)?)/g,': <span class="n">$1</span>');
}
function paint(){
  document.getElementById('tabs').innerHTML=VIEWS.map(([v,label])=>
    '<button data-v="'+v+'" class="'+(v===VIEW?'on':'')+'">'+label+
    (v==='factors'&&LAST.factors?' ('+LAST.factors.length+')':'')+
    (v==='rating'&&LAST.rating?' ('+LAST.rating.coverages.length+')':'')+
    (v==='referrals'&&LAST.referrals?' ('+LAST.referrals.length+')':'')+
    '</button>').join('');
  document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>{
    VIEW=b.dataset.v; paint(); });
  document.getElementById('jsonout').innerHTML=
    colour(JSON.stringify(slice(LAST,VIEW),null,2));
  document.getElementById('jsoncard').style.display='';
}
document.getElementById('copy').onclick=()=>{
  navigator.clipboard.writeText(JSON.stringify(slice(LAST,VIEW),null,2));
  const b=document.getElementById('copy'); b.textContent='Copied';
  setTimeout(()=>b.textContent='Copy',1200); };
// A full run: start it, poll it, and show the result as a table anyone can
// read -- test number, both premiums, and whether they agree.
let POLL=null;
document.getElementById('brun').onclick=()=>{
  const btn=document.getElementById('brun');
  btn.disabled=true; document.getElementById('bprog').style.display='';
  fetch('/api/batch',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({mode:$('#mode').value,rounding:$('#rounding').value,
      compare:document.getElementById('bcmp').checked})})
   .then(r=>r.json()).then(j=>{
     const bar=document.getElementById('bbar'); bar.max=j.total; bar.value=0;
     POLL=setInterval(()=>poll(j.id,btn),1500); poll(j.id,btn);
   });
};
function poll(id,btn){
  fetch('/api/batch/'+id).then(r=>r.json()).then(j=>{
    const bar=document.getElementById('bbar');
    bar.max=j.total; bar.value=j.done;
    document.getElementById('bmsg').textContent=
      j.done+' of '+j.total+(j.finished?' — finished':' — running…');
    batchOut(j);
    if(j.finished){ clearInterval(POLL); btn.disabled=false;
      document.getElementById('bprog').style.display='none'; }
  });
}
function batchOut(j){
  const rows=j.rows, pass=rows.filter(r=>r.status==='PASS').length,
        fail=rows.filter(r=>r.status==='FAIL').length,
        other=rows.filter(r=>r.status!=='PASS'&&r.status!=='FAIL').length,
        done=rows.length, total=j.total;
  const pct=x=>total?(100*x/total)+'%':'0%';
  // A plain-English headline first, then the bar, then the detail.
  let head;
  if(j.compare){
    head='<div class="big">'+pass+' of '+done+' match ISO exactly</div>'+
      (fail?'<div class="muted">'+fail+' differ — every difference is our '+
        'defect until proven otherwise</div>':
       (done===total?'<div class="muted">No differences.</div>':''));
  } else {
    head='<div class="big">'+rows.filter(r=>r.engine).length+' of '+done+
      ' rated</div><div class="muted">Engine only — ISO not called</div>';
  }
  const bar='<div class="bar"><span class="p" style="width:'+pct(pass)+
    '"></span><span class="f" style="width:'+pct(fail)+
    '"></span><span class="u" style="width:'+pct(total-pass-fail)+
    '"></span></div><div class="legend">green: agree &middot; red: differ '+
    '&middot; grey: not yet run</div>';
  const body=table(
    j.compare?['#','State','Our engine','ISO','Difference','Result']
             :['#','State','Our engine','Packages','Referrals'],
    rows.map(r=>{
      const bad=r.status==='FAIL'||r.status.indexOf('ERROR')>=0||
                r.status.indexOf('STOPPED')>=0||r.status.indexOf('UNAVAIL')>=0;
      const verdict=r.status==='PASS'?'<span class="badge pass">Match</span>':
        r.status==='FAIL'?'<span class="badge fail">Differs</span>':
        '<span class="badge na">'+esc(r.status)+'</span>';
      return '<tr'+(bad?' class="rowfail"':'')+'><td>'+r.n+'</td><td><b>'+
        esc(r.juris)+'</b></td><td class="n">'+esc(r.engine||'—')+'</td>'+
        (j.compare
          ?'<td class="n">'+esc(r.iso||'—')+'</td><td class="n">'+
             esc(r.delta&&r.delta!=='0'?r.delta:'')+'</td><td>'+verdict+
             (r.detail?'<div class="muted">'+esc(r.detail)+'</div>':'')+'</td>'
          :'<td class="muted">'+esc(r.packages||'')+'</td><td class="n">'+
             (r.referrals||0)+'</td>')+'</tr>';
    }));
  document.getElementById('bout').innerHTML=
    card('Test results', head+bar+'<div class="scroll">'+body+'</div>');
}
function render(d){
  if(d.error){ out.innerHTML=card('Refused','<div class="stopped">'+esc(d.error)+'</div>'); return; }
  let h='';
  const head='<div class="muted">'+esc(d.jurisdiction)+' as of '+esc(d.asof)+
    ' &middot; '+esc(d.mode)+' &middot; '+esc(d.rounding)+'</div>'+
    '<div class="muted">'+d.packages.map(esc).join(' over ')+'</div>';
  LAST=d; if(d.complete) paint();
  if(!d.complete){
    document.getElementById('jsoncard').style.display='none';
    h+=card('Did not rate', head+'<div class="stopped">'+esc(d.stopped)+'</div>'+
      '<div class="muted">The engine refuses rather than guessing.</div>');
    out.innerHTML=h; return; }
  // The comparison, said plainly: two numbers and whether they agree.
  let cmp='';
  if(d.iso){
    if(!d.iso.available){
      cmp='<div class="muted">ISO comparison unavailable: '+esc(d.iso.reason)+'</div>';
    } else {
      cmp='<div class="verdict"><span class="vs">Our engine</span>'+
        '<b>'+esc(d.premium)+'</b><span class="vs">ISO</span><b>'+
        esc(d.iso.premium)+'</b><span class="badge '+
        (d.iso.agrees?'pass':'fail')+'">'+
        (d.iso.agrees?'They agree':'They differ by '+esc(d.iso.delta))+
        '</span></div>'+
        (d.iso.edition_agrees===false?'<div class="muted">ISO rated with '+
          esc(d.iso.package)+', we resolved '+esc(d.packages[0])+'</div>':'');
    }
  }
  h+=card('Premium', '<div class="premium">'+esc(d.premium)+'</div>'+head+cmp);
  // How it rated: only the factors that participated, in the order the
  // engine computed them, ending in the premium. Zero-valued steps are
  // counted, not hidden -- a zero where a rate belonged is the defect this
  // engine exists to refuse, and a simplified view may not conceal one.
  h+=card('How it rated', (d.rating.coverages||[]).map(c=>
    '<div class="covhead">'+esc(c.coverage.replace(
      'GeneralLiabilityClassification',''))+
    ' <small>subline '+esc(c.subline||'-')+
    ', class '+esc(c.class_code||'-')+'</small></div>'+
    table(['Factor','Value'],
      c.factors.map(f=>'<tr'+(f.milestone?' class="ms"':'')+'><td>'+
        esc(f.factor)+'</td><td class="n">'+esc(f.value)+'</td></tr>')
      .concat(['<tr class="total"><td>Coverage premium</td><td class="n">'+
        esc(c.premium)+'</td></tr>']))+
    (c.omitted_zero.length?'<div class="om">'+c.omitted_zero.length+
      ' factors were zero and are omitted here: '+
      c.omitted_zero.map(esc).join(', ')+'</div>':'')
  ).join('')+
   '<table><tr class="total"><td>Policy premium</td><td class="n">'+
   esc(d.premium)+'</td></tr></table>');
  h+=card('By subline', table(['Subline','Premium'],
    d.by_subline.map(s=>'<tr><td><b>'+esc(s.subline)+'</b></td>'+
      '<td class="n">'+esc(s.premium)+'</td></tr>')));
  h+=card('Referrals ('+d.referrals.length+')', d.referrals.length?
    d.referrals.map(r=>'<div style="margin-bottom:9px"><span class="pill refer">'+
      esc(r.code)+'</span> '+esc(r.condition)+
      (r.clears_with?'<div class="muted">Clears with: <code>'+esc(r.clears_with)+
      '</code></div>':'')+'<div class="muted">'+esc(r.where)+'</div></div>').join('')
    : '<div class="muted">None. In strict-erc mode the register is not applied.</div>');
  if(d.messages.length) h+=card('ISO rating messages',
    d.messages.map(m=>'<div>'+esc(m)+'</div>').join(''));
  if(d.findings.length) h+=card('Submission check',
    '<div class="scroll">'+table(['','Where','Detail'], d.findings.map(f=>
      '<tr><td><span class="pill '+(f.level=='error'?'err':f.level=='warning'?'warn':'info')+
      '">'+esc(f.code)+'</span></td><td><code>'+esc(f.where)+'</code></td><td class="muted">'+
      esc(f.detail)+'</td></tr>'))+'</div>');
  h+=card('Factors', '<div class="muted">'+d.factors.length+
    ' rating factors of '+d.trace_len+
    ' trace entries &mdash; see the Result panel below the submission.</div>');
  out.innerHTML=h;
}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):                    # pragma: no cover - quiet
        pass

    def _tester(self, method, path, query, body=None):
        """Hand the request to `ui.tester`, or return False to keep looking.

        **The tester's routes are not written here.** `ui/` owns its page, its
        charts and its history; this file owns the socket. The whole point of
        keeping them apart is that neither grows the other's concerns -- so the
        mount is four lines and knows nothing about variables or premiums.
        """
        try:
            from ui import tester as ui_tester
        except Exception as exc:                              # noqa: BLE001
            if path.startswith("/api/tester") or path == "/tester":
                self._send(500, json.dumps(
                    {"error": f"tester unavailable: {type(exc).__name__}: {exc}"}))
                return True
            return False
        out = ui_tester.dispatch(method, path, query, body)
        if out is None:
            return False
        code, payload, kind = out
        self._send(code, payload,
                   "text/html" if kind == "html" else "application/json")
        return True

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = dict(parse_qsl(parsed.query))
        if self._tester("GET", path, query):
            return
        if path == "/":
            return self._send(200, PAGE, "text/html")
        if path == "/api/samples":
            js = sorted(p.name for p in SAMPLES.iterdir()
                        if p.is_dir() and (p / "submission.json").exists()) \
                if SAMPLES.is_dir() else []
            return self._send(200, json.dumps({
                "jurisdictions": js, "modes": list(MODES),
                "no_iso": sorted(NO_ISO & set(js))}))
        if path.startswith("/api/batch/"):
            job_id = path.rsplit("/", 1)[-1]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                if job is None:
                    return self._send(404, json.dumps({"error": "no such run"}))
                return self._send(200, json.dumps({
                    "id": job_id, "total": job["total"], "done": job["done"],
                    "finished": job["finished"], "compare": job["compare"],
                    "started": job["started"], "ended": job.get("ended"),
                    "rows": list(job["rows"]),
                }))
        if path.startswith("/api/sample/"):
            f = SAMPLES / path.rsplit("/", 1)[-1] / "submission.json"
            if not f.exists():
                return self._send(404, json.dumps({"error": "no such sample"}))
            return self._send(200, f.read_text(encoding="utf-8"))
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        n = int(self.headers.get("Content-Length") or 0)
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except ValueError as exc:
            return self._send(400, json.dumps({"error": f"bad JSON: {exc}"}))
        if self._tester("POST", path, dict(parse_qsl(parsed.query)), req):
            return
        if path not in ("/api/rate", "/api/batch"):
            return self._send(404, json.dumps({"error": "not found"}))
        mode = req.get("mode", STRICT)
        if mode not in MODES:
            return self._send(400, json.dumps({"error": f"unknown mode {mode}"}))

        if path == "/api/batch":
            compare = bool(req.get("compare"))
            js = req.get("jurisdictions")
            if not js:
                js = sorted(p.name for p in SAMPLES.iterdir()
                            if p.is_dir() and (p / "submission.json").exists())
                # A jurisdiction ISO will not answer for cannot be compared.
                # Leaving it in would report a permanent red row and read as an
                # engine failure, which it is not.
                if compare:
                    js = [j for j in js if j not in NO_ISO]
            job_id = uuid.uuid4().hex[:12]
            with JOBS_LOCK:
                JOBS[job_id] = {"total": len(js), "done": 0, "rows": [],
                                "finished": False, "compare": compare,
                                "started": time.time()}
            threading.Thread(
                target=_batch_worker, daemon=True,
                args=(job_id, js, mode, req.get("rounding", "ROUND_HALF_UP"),
                      compare)).start()
            return self._send(200, json.dumps({"id": job_id, "total": len(js),
                                               "compare": compare}))

        try:
            result = rate(req.get("payload") or {}, mode,
                          req.get("rounding", "ROUND_HALF_UP"),
                          compare=bool(req.get("compare")))
        except Exception as exc:                            # noqa: BLE001
            # A refusal is a legitimate answer and is shown as one, not as a
            # server error -- the engine declining to guess is the product.
            return self._send(200, json.dumps(
                {"error": f"{type(exc).__name__}: {exc}"}))
        return self._send(200, json.dumps(result))


def main(argv) -> int:
    port = int(argv[0]) if argv else PORT
    srv = ThreadingHTTPServer((HOST, port), Handler)
    url = f"http://{HOST}:{port}"
    print(f"GL rating engine UI on {url}")
    print(f"  {len(RESOLVER.packages)} packages loaded; "
          f"{len(list(SAMPLES.iterdir())) if SAMPLES.is_dir() else 0} samples")
    print("  Ctrl-C to stop")
    if "--no-browser" not in argv:
        try:
            webbrowser.open(url)
        except Exception:                                   # noqa: BLE001
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
