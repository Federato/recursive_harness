#!/usr/bin/env python
"""Render selected project Markdown documents into one self-contained, tabbed HTML page.

    python scripts/build_docs_html.py

Output: docs/GL-RATING-ENGINE-DOCS.html  (no external assets, opens offline)
"""
import os, re, sys, html, datetime
import markdown

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOCS = [
    ("exec", "Executive summary",                    "docs/EXECUTIVE-SUMMARY.md"),
    ("prd",  "Product Requirements (plain language)", "docs/PRD-GL-RATING-ENGINE.md"),
    ("plan", "Python Build Plan (technical)",         "docs/GL-RATING-ENGINE-BUILD-PLAN.md"),
    ("stages","The Build — staged plan",             "docs/BUILD-STAGES.md"),
    ("blog", "Build diary",                        "BUILD-LOG.md"),
    ("test", "How to test it",                     "TESTING.md"),
    ("pause","Where we paused - 12 Aug",           "docs/WHERE-WE-PAUSED-2026-08-12.md"),
    ("p2b",  "From planning to build",             "docs/FROM-PLANNING-TO-BUILD.md"),
    ("recon", "Reconciliation — what the gates changed", "docs/gates/RECONCILIATION.md"),
    ("oi40", "OI-40 — every count re-measured as-of a date", "docs/gates/OI-40-ASOF-RECOUNT.md"),
    ("sizing", "Phase sizing, measured",                     "docs/PHASE-SIZING.md"),
    ("g334", "Gate — 334 Premises/Operations",        "docs/gates/GATE-334-PREMISES-OPERATIONS.md"),
    ("g335", "Gate — 335 OCP / Principals Protective", "docs/gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md"),
    ("g336", "Gate — 336 Products/Compl. Operations", "docs/gates/GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md"),
    ("g332", "Gate — 332 Liquor Liability",          "docs/gates/GATE-332-LIQUOR-LIABILITY.md"),
    ("g335rr", "Gate — 335 Railroad Protective",     "docs/gates/GATE-335-RAILROAD-PROTECTIVE.md"),
    ("g365", "Gate — 365 Withdrawal / LoED / Cyber", "docs/gates/GATE-365-WITHDRAWAL-LOED-CYBER.md"),
    ("g370", "Gate — 370 Unmanned Aircraft",        "docs/gates/GATE-370-UNMANNED-AIRCRAFT.md"),
    ("gsor", "Gate — Size-Of-Risk",                 "docs/gates/GATE-SIZE-OF-RISK.md"),
    ("gter", "Gate — Terrorism",                    "docs/gates/GATE-TERRORISM.md"),
    ("ca",   "California differential",             "docs/gates/CALIFORNIA-DIFFERENTIAL.md"),
    ("ny",   "New York differential",               "docs/gates/NEW-YORK-DIFFERENTIAL.md"),
    ("gplan","Gate — Rating plans",                 "docs/gates/GATE-RATING-PLANS.md"),
    ("gst",  "Gate — State-specific coverages",     "docs/gates/GATE-STATE-SPECIFIC.md"),
]

EXT = ["tables", "fenced_code", "toc", "sane_lists", "attr_list"]


def render(path):
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    md = markdown.Markdown(extensions=EXT, extension_configs={"toc": {"toc_depth": "2-3"}})
    body = md.convert(src)
    # ~~strike~~ is not in core python-markdown
    body = re.sub(r"~~(.+?)~~", r"<del>\1</del>", body, flags=re.S)
    return body, md.toc, len(src.split())


CSS = """
:root{--bg:#fbfbfd;--fg:#1d1d20;--mut:#63636b;--line:#e3e3e8;--accent:#1f3864;
--code-bg:#f4f4f7;--tbl-head:#1f3864;--mark:#fff3cd;--del:#a11}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
background:var(--bg);color:var(--fg)}
header{background:var(--accent);color:#fff;padding:22px 32px 0}
header h1{margin:0 0 4px;font-size:20px;font-weight:650;letter-spacing:-.01em}
header .sub{opacity:.72;font-size:13px;margin-bottom:16px}
nav{display:flex;gap:4px}
nav button{appearance:none;border:0;background:rgba(255,255,255,.10);color:#fff;cursor:pointer;
font:inherit;font-size:14px;padding:10px 18px;border-radius:7px 7px 0 0;opacity:.75}
nav button:hover{opacity:1;background:rgba(255,255,255,.18)}
nav button[aria-selected="true"]{background:var(--bg);color:var(--accent);font-weight:640;opacity:1}
.wrap{display:grid;grid-template-columns:250px minmax(0,1fr);gap:34px;
max-width:1360px;margin:0 auto;padding:30px 32px 90px}
aside{position:sticky;top:22px;align-self:start;max-height:calc(100vh - 50px);overflow:auto;
font-size:13.5px;border-left:2px solid var(--line);padding-left:14px}
aside .lbl{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--mut);
font-weight:700;margin-bottom:9px}
aside ul{list-style:none;margin:0;padding:0}
aside ul ul{padding-left:13px}
aside a{color:var(--mut);text-decoration:none;display:block;padding:3px 0;line-height:1.4}
aside a:hover{color:var(--accent)}
article{min-width:0;background:#fff;border:1px solid var(--line);border-radius:11px;padding:34px 42px 54px}
article h1{font-size:27px;margin:0 0 8px;letter-spacing:-.02em}
article h2{font-size:20px;margin:38px 0 12px;padding-bottom:7px;border-bottom:1px solid var(--line);
letter-spacing:-.01em}
article h3{font-size:16.5px;margin:26px 0 9px}
article h4{font-size:15px;margin:20px 0 7px;color:var(--mut)}
p,li{max-width:74ch}
code{background:var(--code-bg);padding:.13em .38em;border-radius:4px;
font:13.5px/1.5 "SF Mono",Consolas,"Liberation Mono",Menlo,monospace}
pre{background:var(--code-bg);border:1px solid var(--line);border-radius:8px;padding:14px 17px;
overflow-x:auto}
pre code{background:none;padding:0;font-size:13px;line-height:1.55}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14.2px;display:block;overflow-x:auto}
th{background:var(--tbl-head);color:#fff;text-align:left;font-weight:600;padding:9px 12px;
white-space:nowrap}
td{border-bottom:1px solid var(--line);padding:9px 12px;vertical-align:top}
tr:nth-child(even) td{background:#fafafc}
blockquote{margin:16px 0;padding:12px 18px;background:#f6f8fc;border-left:4px solid var(--accent);
border-radius:0 7px 7px 0}
blockquote p{margin:.45em 0}
del{color:var(--del);text-decoration-thickness:1px}
hr{border:0;border-top:1px solid var(--line);margin:30px 0}
a{color:var(--accent)}
.meta{font-size:12.5px;color:var(--mut);margin:0 0 22px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.panel[hidden]{display:none}
@media(max-width:1000px){.wrap{grid-template-columns:1fr;padding:20px}aside{display:none}
article{padding:24px 20px 40px}}
@media print{header,aside,nav{display:none}.wrap{display:block;padding:0}
article{border:0;padding:0}.panel[hidden]{display:block!important}}
"""

JS = """
const tabs=[...document.querySelectorAll('nav button')];
function show(id){
  tabs.forEach(b=>b.setAttribute('aria-selected',String(b.dataset.t===id)));
  document.querySelectorAll('.panel').forEach(p=>p.hidden=(p.id!=='p-'+id));
  document.querySelectorAll('.toc').forEach(t=>t.hidden=(t.id!=='t-'+id));
  history.replaceState(null,'','#'+id);
  window.scrollTo({top:0});
}
tabs.forEach(b=>b.onclick=()=>show(b.dataset.t));
show((location.hash||'#prd').slice(1).split('&')[0]||'prd');
"""


def main():
    panels, tocs, navs = [], [], []
    for i, (key, label, path) in enumerate(DOCS):
        body, toc, words = render(path)
        navs.append(f'<button data-t="{key}" aria-selected="{"true" if i==0 else "false"}">'
                    f'{html.escape(label)}</button>')
        meta = (f'Source: <code>{html.escape(path)}</code> &nbsp;·&nbsp; '
                f'{words:,} words &nbsp;·&nbsp; rendered '
                f'{datetime.date.today().isoformat()}')
        panels.append(f'<div class="panel" id="p-{key}"{"" if i==0 else " hidden"}>'
                      f'<p class="meta">{meta}</p>{body}</div>')
        tocs.append(f'<div class="toc" id="t-{key}"{"" if i==0 else " hidden"}>'
                    f'<div class="lbl">On this page</div>{toc}</div>')

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GL Rating Engine — Documentation</title><style>{CSS}</style></head><body>
<header><h1>ISO General Liability Rating Engine</h1>
<div class="sub">Recursive Harness 2.0 — product requirements and build plan</div>
<nav>{''.join(navs)}</nav></header>
<div class="wrap"><aside>{''.join(tocs)}</aside><article>{''.join(panels)}</article></div>
<script>{JS}</script></body></html>"""

    out = os.path.join(ROOT, "docs", "GL-RATING-ENGINE-DOCS.html")
    open(out, "w", encoding="utf-8").write(page)
    print(f"wrote {out}  ({os.path.getsize(out)/1024:.0f} KB)")
    for _, label, path in DOCS:
        print(f"   tab: {label}  <- {path}")


if __name__ == "__main__":
    main()
