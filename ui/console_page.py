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
    console_page.dispatch(method, path, query, body)   # mounted through ui.tester
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from console import ledger, status

from . import variables

#: The seven screens (the brief's order), the hash each opens on, and the task that builds it.
SCREENS = (
    ("board", "Coverage Board", "TC-18"),
    ("matrix", "Readiness Matrix", "TC-16"),
    ("plan", "Test Plan Builder", "TC-27"),
    ("trace", "Trace Diff", "TC-21"),
    ("workbench", "Scenario Workbench", "TC-23"),
    ("library", "Regression Library", "TC-33"),
    ("queue", "Queue & Run Log", "TC-31"),
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
        "queued": 0,                     # the dispatcher (TC-30) owns a queue; none exists yet
        "overrides": overrides,
        "resets_at": reset.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resets_in_s": int((reset - now).total_seconds()),
        "lanes": [{"key": k, "name": LANE_NAMES[k], "cap": c, "used": u.get(k, 0)}
                  for k, c in ledger.LANES.items()],
    }


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
    if method != "GET":
        return None
    if path == "/console":
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
    if path == "/api/console/controls":
        return 200, json.dumps(controls(_line(query))), "json"
    if path == "/api/console/readiness":
        from console import readiness
        return 200, json.dumps(readiness.get(query.get("lob"), query.get("state"),
                                             force=query.get("refresh") == "1")), "json"
    return None


def page() -> str:
    tabs = "".join(f'<a class="tab" href="#{k}" data-k="{k}">{label.replace("&", "&amp;")}</a>'
                   for k, label, _ in SCREENS)
    screens = "".join(
        BUILT.get(k) or (f'<section class="screen" id="s-{k}" hidden><div class="eyebrow">Screen {i} of 7</div>'
                         f'<h1>{label.replace("&", "&amp;")}</h1><div class="pending">Built in {task} '
                         f'(docs/TC-PLAN.md).<span class="filter"></span></div></section>')
        for i, (k, label, task) in enumerate(SCREENS, 1))
    return (PAGE.replace("{{TABS}}", tabs).replace("{{SCREENS}}", screens)
            .replace("/*{{CSS}}*/", MATRIX_CSS + BOARD_CSS).replace("/*{{JS}}*/", MATRIX_JS + BOARD_JS)
            .replace("{{BOOT}}", json.dumps({"cap": cap(), "legend": legend(), "names": STATE_NAMES})))


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
    const ls=[...new Set(L.map(g=>g.lob))],ss=[...new Set(L.map(g=>g.state))];
    location.hash='#plan?from='+encodeURIComponent('Readiness Matrix gaps')+'&lines='+encodeURIComponent(ls.join(','))+'&states='+encodeURIComponent(ss.length+' states')+'&cells='+L.length;};
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
  <div class="brand"><b>ISO Rating Test Console</b><span>Internal engine vs. ISO RaaS (UAT) · GL &amp; CP</span></div>
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
  const [k,q]=(location.hash||'#matrix').slice(1).split('?');
  const ok=document.getElementById('s-'+k)?k:'matrix';
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
.bd-stats{grid-template-columns:1fr 1fr 1.6fr 1fr 1fr}
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
    cols.forEach(p=>{const v=r.cells[p.id]||['untested',0,0],t=bdCellTxt(v),k=r.state+'|'+p.id;
      h+='<button class="bd-c chip '+v[0]+(BD.sel===k?' sel':'')+'" data-k="'+esc(k)+'" title="'+esc(r.state+' · '+p.label+' · '+(v[0]==='descoped'?'descoped':LG[v[0]].board)+(v[1]?' · '+v[1]+' scenario'+(v[1]>1?'s':''):''))+'"><i>'+esc(t[0])+'</i>'+(t[1]?'<small>'+t[1]+'</small>':'')+'</button>';});
  });
  g.innerHTML=h;
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
    '<button class="btn" id="bd-tomx" style="margin-top:auto">See '+st+' on the Readiness Matrix</button>';
  document.getElementById('bd-back').onclick=ev=>{ev.preventDefault();BD.state=null;BD.sel=null;bdDraw();};
  document.getElementById('bd-tomx').onclick=()=>{location.hash='#matrix';};
}
function bdCell(k,fetchIt){
  const st=k.split('|')[0],pid=k.split('|')[1];
  if(fetchIt===false&&BD.cell&&BD.cell.key===k)return bdCellDraw(BD.cell);
  document.getElementById('bd-side').innerHTML='<div class="mx-msg">Loading the scenarios…</div>';
  fetch('/api/console/board/cell?lob='+BD.line+'&state='+st+'&path='+encodeURIComponent(pid)).then(r=>r.json())
    .then(c=>{c.key=k;BD.cell=c;if(BD.sel===k)bdCellDraw(c);});
}
function bdCellDraw(c){
  const s=c.status==='descoped'?{glyph:'⊘',board:'Descoped',meaning:'taken out of scope with a reason'}:LG[c.status];
  let h='<a href="#" class="mx-back" id="bd-back">← '+esc(BOOT.names[c.state]||c.state)+'</a><div class="cap2">Selected cell · '+esc(c.line+' · '+c.state)+'</div>'+
    '<div style="display:flex;gap:10px;align-items:center"><span class="chip '+c.status+'">'+esc(s.glyph)+'</span><h2 style="font-size:19px">'+esc(c.label)+'</h2></div>'+
    '<div class="mx-msg">'+esc(s.board+' — '+s.meaning)+'</div>';
  if(!c.applies)h+='<div class="mx-msg">Not filed in '+esc(c.state)+': '+esc(c.why||'the state files no such path')+' (D5).</div>';
  else if(!c.scenarios.length)h+='<div class="mx-msg">No scenario has walked this path in '+esc(c.state)+' yet.</div>';
  else h+='<div class="cap2">Scenarios · '+c.scenarios.length+'</div><table class="bd-tbl"><tr><td><b>Scenario</b></td><td class="st"><b>State</b></td><td><b>Ours / ISO</b></td></tr>'+
    c.scenarios.map(x=>'<tr><td>'+esc(x.scenario)+'<div class="mx-msg">'+esc((x.source||'')+(x.at?' · '+x.at.slice(0,10):''))+'</div></td>'+
      '<td class="st">'+(x.status==='inert'?'<span class="mx-msg">inert</span>':'<span class="chip '+x.status+'">'+esc(LG[x.status].glyph)+'</span>')+'</td>'+
      '<td>'+esc(x.ours==null?'—':x.ours)+' / '+esc(x.iso==null?'—':x.iso)+(x.delta&&+x.delta!==0?'<div class="mx-msg">Δ '+esc((+x.delta>0?'+':'')+x.delta)+(x.category?' · '+esc(x.category.replace(/_/g,' ')):' · unclassified')+'</div>':'')+'</td></tr>').join('')+'</table>'+
    '<div class="mx-msg">Trace Diff (TC-21) will open a scenario step by step.</div>';
  document.getElementById('bd-side').innerHTML=h;
  document.getElementById('bd-back').onclick=ev=>{ev.preventDefault();BD.sel=null;BD.state=c.state;bdDraw();};
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
if((location.hash||'').startsWith('#board'))bdRoute();
setInterval(()=>{if(!document.getElementById('s-board').hidden&&BD.data)bdLoad().catch(()=>{});},60000);
"""
