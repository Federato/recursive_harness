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
import webbrowser
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from gl_engine import EditionResolver                       # noqa: E402
from gl_engine.interp import tree                           # noqa: E402
from gl_engine.rating import Kernel, MODES, STRICT          # noqa: E402
from gl_engine.schema import Schema, validate               # noqa: E402
from gl_engine.resolve import ResolvedBook                  # noqa: E402

SAMPLES = ROOT / "Engine_Payloads"
HOST, PORT = "127.0.0.1", 8765

#: Built once. Discovery is ~1s and every rating would otherwise pay it.
RESOLVER = EditionResolver()
KERNELS = {m: Kernel(mode=m, resolver=RESOLVER) for m in MODES}

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


def rate(payload: dict, mode: str, rounding: str) -> dict:
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
header{background:#1f2933;color:#fff;padding:14px 22px}
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
</style></head><body>
<header><h1>GL Rating Engine</h1>
<span>ISO content, executed &mdash; every number carries its source</span></header>
<div class="wrap">
 <div class="col">
  <div class="card"><h2>Submission</h2><div class="body">
   <div class="row">
    <select id="sample"><option value="">Load a sample&hellip;</option></select>
    <select id="mode"></select>
    <select id="rounding">
     <option>ROUND_HALF_UP</option><option>ROUND_HALF_EVEN</option>
     <option>ROUND_DOWN</option></select>
    <button id="go">Rate</button>
   </div>
   <textarea id="payload" spellcheck="false"
     placeholder="Paste a RAaS submission, or load a sample"></textarea>
  </div></div>
  <div class="card" id="jsoncard" style="display:none"><h2>Result
   <button class="copy" id="copy">Copy</button></h2><div class="body">
   <div class="tabs" id="tabs"></div>
   <pre class="json" id="jsonout"></pre>
  </div></div>
 </div>
 <div class="col" id="out"></div>
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
    body:JSON.stringify({payload:p,mode:$('#mode').value,rounding:$('#rounding').value})})
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
  h+=card('Premium', '<div class="premium">'+esc(d.premium)+'</div>'+head);
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

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self._send(200, PAGE, "text/html")
        if path == "/api/samples":
            js = sorted(p.name for p in SAMPLES.iterdir()
                        if p.is_dir() and (p / "submission.json").exists()) \
                if SAMPLES.is_dir() else []
            return self._send(200, json.dumps({"jurisdictions": js,
                                               "modes": list(MODES)}))
        if path.startswith("/api/sample/"):
            f = SAMPLES / path.rsplit("/", 1)[-1] / "submission.json"
            if not f.exists():
                return self._send(404, json.dumps({"error": "no such sample"}))
            return self._send(200, f.read_text(encoding="utf-8"))
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if urlparse(self.path).path != "/api/rate":
            return self._send(404, json.dumps({"error": "not found"}))
        n = int(self.headers.get("Content-Length") or 0)
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except ValueError as exc:
            return self._send(400, json.dumps({"error": f"bad JSON: {exc}"}))
        mode = req.get("mode", STRICT)
        if mode not in MODES:
            return self._send(400, json.dumps({"error": f"unknown mode {mode}"}))
        try:
            result = rate(req.get("payload") or {}, mode,
                          req.get("rounding", "ROUND_HALF_UP"))
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
