"""Render the navigable premium tree from 02's JSON.

    python scripts/premium/03_premium_tree_html.py --line GL
    python scripts/premium/03_premium_tree_html.py --line CF

Writes <LINE>_Algorithm/<LINE>_Premium_Tree.html -- self-contained, no external
requests. Collapsible, searchable, with a jurisdiction selector."""
import json, io, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


import argparse
LINES = {"GL": ("GeneralLiability", "GL", "GL_Algorithm", "terrorism, liquor, unmanned"),
         "CF": ("CommercialProperty", "CP", "CF_Algorithm", "spoilage, earthquake, business income")}
_ap = argparse.ArgumentParser()
_ap.add_argument("--line", choices=sorted(LINES), default="GL")
_A = _ap.parse_args()
ROOTNAME, ABBR, OUTDIR, HINT = LINES[_A.line]
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
J = os.path.join(HERE, "_tree_%s.json" % _A.line)
OUT = os.path.join(REPO, OUTDIR, "%s_Premium_Tree.html" % _A.line)

d = json.load(io.open(J, encoding="utf-8"))
nodes = d["nodes"]
n_nodes = len(nodes)
n_agg = sum(1 for v in nodes.values() if v["a"])
n_sp = sum(1 for v in nodes.values() if v["s"])
n_states = len(d["stateCounts"])
n_only = len({g for lst in d["stateOnly"].values() for g in lst})

CSS = """
:root{--bg:#fbfbfd;--fg:#1d1d20;--mut:#63636b;--line:#e3e3e8;--accent:#1f3864;
--chip:#eef1f6;--agg:#1f3864;--leaf:#6b7280;--ov:#a53d26;--new:#2f7d5a;--code:#f4f4f7}
@media (prefers-color-scheme:dark){:root{--bg:#14181d;--fg:#dfe4e9;--mut:#93a0ad;--line:#2f3740;
--chip:#222a33;--accent:#9fc6e8;--agg:#9fc6e8;--leaf:#8b95a1;--ov:#e08a70;--new:#63c090;--code:#222a33}}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
background:var(--bg);color:var(--fg)}
header{background:var(--accent);color:#fff;padding:18px 26px}
@media (prefers-color-scheme:dark){header{background:#1b2530}}
header h1{margin:0 0 3px;font-size:19px;font-weight:650}
header .sub{opacity:.8;font-size:13px}
.stats{display:flex;flex-wrap:wrap;gap:18px;margin-top:12px;font-size:12.5px}
.stats b{font-size:16px;display:block;font-weight:700}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:12px 26px;
border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
input,select{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:6px;
background:var(--bg);color:var(--fg)}
input{min-width:280px}
button{font:inherit;padding:6px 12px;border:1px solid var(--line);border-radius:6px;
background:var(--chip);color:var(--fg);cursor:pointer}
button:hover{border-color:var(--accent)}
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:0;align-items:start}
@media(max-width:1100px){.wrap{grid-template-columns:1fr}}
#tree{padding:14px 26px 70px;overflow-x:auto}
aside{border-left:1px solid var(--line);padding:18px 22px 70px;position:sticky;top:57px;
max-height:calc(100vh - 57px);overflow:auto}
.node{margin:1px 0}
.row{display:flex;align-items:center;gap:7px;padding:3px 6px;border-radius:5px;cursor:pointer;
white-space:nowrap}
.row:hover{background:var(--chip)}
.row.sel{background:var(--chip);outline:1px solid var(--accent)}
.tw{width:15px;text-align:center;color:var(--mut);font-size:11px;user-select:none}
.nm{font-family:ui-monospace,Consolas,monospace;font-size:12.5px}
.kids{margin-left:17px;border-left:1px dotted var(--line);padding-left:9px}
.chip{font-size:10.5px;padding:1px 6px;border-radius:9px;background:var(--chip);color:var(--mut);
font-weight:600;letter-spacing:.02em}
.chip.agg{color:var(--agg)} .chip.leaf{color:var(--leaf)}
.chip.ov{background:rgba(165,61,38,.14);color:var(--ov)}
.chip.own{color:var(--new)}
.hid{display:none}
h3{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin:20px 0 7px}
aside h2{font-family:ui-monospace,Consolas,monospace;font-size:14px;margin:0 0 4px;word-break:break-all}
dl{margin:0;font-size:13px} dt{color:var(--mut);font-size:11.5px;text-transform:uppercase;
letter-spacing:.05em;margin-top:11px} dd{margin:2px 0 0}
code{font-family:ui-monospace,Consolas,monospace;font-size:12px;background:var(--code);
padding:1px 5px;border-radius:3px}
.path{font-family:ui-monospace,Consolas,monospace;font-size:11.5px;line-height:1.7;word-break:break-all}
.muted{color:var(--mut)} .count{color:var(--mut);font-size:11.5px}
ul.plain{list-style:none;margin:6px 0;padding:0;font-size:12px}
ul.plain li{padding:2px 0;font-family:ui-monospace,Consolas,monospace;word-break:break-all}
.note{background:var(--chip);border-left:3px solid var(--accent);padding:9px 12px;
border-radius:0 5px 5px 0;font-size:12.5px;margin:10px 0}
"""

JS = """
const D = DATA, N = D.nodes;
let sel = null, state = 'CW', filter = '';
const open = new Set([D.root]);

function kidsOf(g){ return (N[g] ? N[g].c : []).slice().sort(); }
function pathTo(g){ const p=[]; let cur=g, guard=0;
  while(cur && cur!==D.root && guard++<10){ const par=Object.keys(N).find(k=>N[k].c.includes(cur));
    if(!par) break; p.push(par); cur=par; } return p; }

function matches(g){
  if(!filter) return true;
  if(g.toLowerCase().includes(filter)) return true;
  return kidsOf(g).some(matches);
}

function render(){
  const host = document.getElementById('tree');
  host.innerHTML = '';
  if(filter && !matches(D.root)){
    host.innerHTML = '<div class="note">No premium group matches <b>'+filter+'</b>.</div>';
    document.getElementById('shown').textContent = 'no matches'; return;
  }
  host.appendChild(nodeEl(D.root));
  const n = host.querySelectorAll('.row').length;
  document.getElementById('shown').textContent =
    n + ' node' + (n===1?'':'s') + ' shown' + (filter ? ' (filtered)' : '');
}

function nodeEl(g){
  const n = N[g], wrap = document.createElement('div'); wrap.className='node';
  const row = document.createElement('div'); row.className='row'+(sel===g?' sel':'');
  const kids = kidsOf(g).filter(matches);
  const tw = document.createElement('span'); tw.className='tw';
  tw.textContent = kids.length ? (open.has(g)?'\\u25be':'\\u25b8') : '\\u00b7';
  tw.onclick = e => { e.stopPropagation(); if(!kids.length) return;
                      open.has(g)?open.delete(g):open.add(g); render(); };
  row.appendChild(tw);
  const nm = document.createElement('span'); nm.className='nm';
  nm.textContent = g.replace(/^GeneralLiability/,'GL\\u00b7');
  row.appendChild(nm);
  row.appendChild(chip(n.a?'agg':'leaf', n.a?'agg':'leaf'));
  if(n.o) row.appendChild(chip('own premium','own'));
  if(n.s) row.appendChild(chip('SetPremium',''));
  const ov = (n.ov||[]).filter(s => state==='CW' || s===state);
  if(ov.length) row.appendChild(chip('override: '+ov.join(' '),'ov'));
  if(kids.length){ const c=document.createElement('span'); c.className='count';
                   c.textContent='('+kids.length+')'; row.appendChild(c); }
  row.onclick = () => { sel=g; render(); detail(g); };
  wrap.appendChild(row);
  if(open.has(g) && kids.length){
    const k=document.createElement('div'); k.className='kids';
    kids.forEach(c=>k.appendChild(nodeEl(c)));
    wrap.appendChild(k);
  }
  return wrap;
}

function chip(text, cls){ const s=document.createElement('span');
  s.className='chip '+(cls||''); s.textContent=text; return s; }

function detail(g){
  const n=N[g], a=document.getElementById('detail');
  const p=pathTo(g);
  let h = '<h2>'+g+'</h2>';
  h += '<dl>';
  h += '<dt>Role</dt><dd>'+(n.a?'Aggregator \\u2014 writes <code>ErcCalculatedTotalPremium</code>'
        :'Leaf \\u2014 contributes its own <code>Premium</code>')+'</dd>';
  h += '<dt>Depth below the account total</dt><dd>'+n.d+'</dd>';
  h += '<dt>Path to the account total</dt><dd class="path">'+
       (p.length? p.join(' \\u2192 ') : '<span class="muted">this is the account total</span>')+'</dd>';
  h += '<dt>Children summed</dt><dd>'+n.c.length+
       ' <span class="muted">('+n.rep+' repeating via ForEach, '+n.sing+' singleton via Locate)</span></dd>';
  h += '<dt>Contributes own Premium</dt><dd>'+(n.o?'yes':'no')+'</dd>';
  h += '<dt>SetPremium</dt><dd>'+(n.s? n.s.toLocaleString()+' chars'
        :'<span class="muted">none \\u2014 this group computes no premium of its own</span>')+'</dd>';
  if(n['in'] && n['in'].length){
    h += '<dt>Fields SetPremium reads</dt><dd><ul class="plain">'+
         n['in'].map(x=>'<li>'+x+'</li>').join('')+'</ul></dd>'; }
  if(n.ov && n.ov.length){
    h += '<dt>States that rewrite this SetPremium</dt><dd><b>'+n.ov.join(', ')+'</b></dd>'; }
  h += '</dl>';
  a.innerHTML = h;
}

function statePanel(){
  const p=document.getElementById('statepanel');
  if(state==='CW'){
    p.innerHTML='<div class="note">Showing the <b>countrywide</b> tree. Pick a state to see what '
      +'its package adds on top, and which premium formulas it rewrites.</div>'; return; }
  const sc=D.stateCounts[state], only=(D.stateOnly[state]||[]);
  const ovg=Object.keys(D.overrideGroups).filter(g=>D.overrideGroups[g].includes(state));
  let h='<div class="note"><b>'+state+'</b> \\u2014 '+sc.pkg+', effective '+sc.eff+'</div><dl>';
  h+='<dt>Premium groups in this package</dt><dd>'+sc.groups+'</dd>';
  h+='<dt>Groups countrywide does not have</dt><dd>'+only.length+'</dd>';
  h+='<dt>Countrywide formulas it rewrites</dt><dd>'+(ovg.length||'none')+'</dd></dl>';
  if(ovg.length) h+='<h3>Rewritten</h3><ul class="plain">'+ovg.map(g=>'<li>'+g+'</li>').join('')+'</ul>';
  if(only.length) h+='<h3>State-only premium groups</h3><ul class="plain">'
      +only.map(g=>'<li>'+g+'</li>').join('')+'</ul>';
  p.innerHTML=h;
}

document.getElementById('q').oninput = e => {
  filter=e.target.value.trim().toLowerCase();
  if(filter){ Object.keys(N).forEach(g=>{ if(g.toLowerCase().includes(filter))
      pathTo(g).forEach(x=>open.add(x)); }); }
  render();
};
document.getElementById('st').onchange = e => { state=e.target.value; statePanel(); render(); };
document.getElementById('expand').onclick = () => {
  Object.keys(N).forEach(g=>{ if(N[g].d<2) open.add(g); }); render(); };
document.getElementById('collapse').onclick = () => {
  open.clear(); open.add(D.root); render(); };
render(); statePanel(); detail(D.root);
"""

opts = "".join('<option value="%s">%s</option>' % (s, s)
               for s in ["CW"] + sorted(d["stateCounts"]))

html = """<title>__LINE__ premium tree &mdash; derivation and roll-up</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>%s</style>
<header>
  <h1>__LINE__ premium tree</h1>
  <div class="sub">%s &middot; every premium group and how it reaches
  <code style="background:rgba(255,255,255,.15);color:#fff">__ROOTNAME__.ErcCalculatedTotalPremium</code></div>
  <div class="stats">
    <div><b>%d</b>groups in the tree</div>
    <div><b>%d</b>aggregators</div>
    <div><b>%d</b>compute a premium</div>
    <div><b>__DEPTH__</b>levels deep</div>
    <div><b>%d</b>jurisdictions analysed</div>
    <div><b>%d</b>state-only premium groups</div>
  </div>
</header>
<div class="bar">
  <input id="q" placeholder="Filter groups \u2014 e.g. __HINT__">
  <select id="st">%s</select>
  <button id="expand">Expand top levels</button>
  <button id="collapse">Collapse all</button>
  <span class="count" id="shown"></span>
</div>
<div class="wrap">
  <div id="tree"></div>
  <aside>
    <h3>Selected node</h3><div id="detail"></div>
    <h3>Jurisdiction</h3><div id="statepanel"></div>
  </aside>
</div>
<script>const DATA=%s;</script>
<script>%s</script>
""" % (CSS, d["pkg"], n_nodes, n_agg, n_sp, n_states, n_only,
       opts, json.dumps(d, separators=(",", ":")), JS)

maxdepth = max(v["d"] for v in nodes.values() if isinstance(v.get("d"), int))
html = (html.replace("__LINE__", _A.line).replace("__ROOTNAME__", ROOTNAME)
            .replace("__ABBR__", ABBR).replace("__HINT__", HINT)
            .replace("__DEPTH__", str(maxdepth)))
io.open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
print("nodes", n_nodes, "| aggregators", n_agg, "| with SetPremium", n_sp,
      "| states", n_states, "| state-only groups", n_only)
