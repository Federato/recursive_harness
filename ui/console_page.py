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
    return [{"key": s.key, "glyph": s.glyph, "board": s.board, "matrix": s.matrix, "meaning": s.meaning}
            for s in status.ALL]


def dispatch(method: str, path: str, query: dict, body):
    """Handle a console route, or return None so the caller keeps looking."""
    if method != "GET":
        return None
    if path == "/console":
        return 200, page(), "html"
    if path == "/api/console/cap":
        return 200, json.dumps(cap()), "json"
    if path == "/api/console/legend":
        return 200, json.dumps(legend()), "json"
    if path == "/api/console/readiness":
        from console import readiness
        return 200, json.dumps(readiness.get(query.get("lob"), query.get("state"),
                                             force=query.get("refresh") == "1")), "json"
    return None


def page() -> str:
    tabs = "".join(f'<a class="tab" href="#{k}" data-k="{k}">{label.replace("&", "&amp;")}</a>'
                   for k, label, _ in SCREENS)
    screens = "".join(
        f'<section class="screen" id="s-{k}" hidden><div class="eyebrow">Screen {i} of 7</div>'
        f'<h1>{label.replace("&", "&amp;")}</h1><div class="pending">Built in {task} '
        f'(docs/TC-PLAN.md).</div></section>'
        for i, (k, label, task) in enumerate(SCREENS, 1))
    return PAGE.replace("{{TABS}}", tabs).replace("{{SCREENS}}", screens).replace(
        "{{BOOT}}", json.dumps({"cap": cap(), "legend": legend()}))


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
  const k=(location.hash||'#matrix').slice(1);
  const ok=document.getElementById('s-'+k)?k:'matrix';
  document.querySelectorAll('.screen').forEach(s=>s.hidden=s.id!=='s-'+ok);
  document.querySelectorAll('.tab').forEach(t=>t.dataset.k===ok?t.setAttribute('aria-current','page'):t.removeAttribute('aria-current'));
}
drawCap(BOOT.cap);drawLegend(BOOT.legend);route();
addEventListener('hashchange',route);
setInterval(()=>fetch('/api/console/cap').then(r=>r.json()).then(drawCap).catch(()=>{}),30000);
</script>
</body></html>"""
