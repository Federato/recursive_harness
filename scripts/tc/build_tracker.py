#!/usr/bin/env python3
"""Build docs/TC-TRACKER.html from docs/TC-PLAN.md.

TC-PLAN.md stays the one place task status is edited; this page is generated
from it. A PostToolUse hook (.claude/settings.json) re-runs it whenever the
plan is edited, and the page reloads itself every 30 seconds, so an open tab
keeps up without anyone touching it.

    python scripts/tc/build_tracker.py            # build
    python scripts/tc/build_tracker.py --hook     # hook mode: build only if stdin names TC-PLAN.md
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "TC-PLAN.md"
OUT = ROOT / "docs" / "TC-TRACKER.html"

ROW = re.compile(r"^\|\s*(TC-\d+)\s*\|(.*)\|(.*)\|(.*)\|\s*$")
RC_HEAD = re.compile(r"^###\s+(RC-\d+)\s*·\s*(.+?)\s*\((\d+) tasks?\)")
MS_HEAD = re.compile(r"^##\s+Milestone\s+(\d+):\s*(.+)$")
GATE = re.compile(r"^\*\*Gate (RC-\d+)(.*?):?\*\*:?\s*(.*)$")
DECISION = re.compile(r"^\|\s*D\d+\s*\|")


def inline(md: str) -> str:
    """The little markdown the plan uses: bold, code, links."""
    s = html.escape(md.strip())
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


def status_of(cell: str) -> tuple[str, str]:
    c = cell.strip()
    if c.startswith("✅"):
        return "done", c.replace("✅", "").strip()
    if c.startswith(("🔄", "🟡", "⏳")) or "progress" in c.lower():
        return "now", re.sub(r"^\S+\s*", "", c)
    if c.startswith(("⛔", "❌")) or "blocked" in c.lower():
        return "blocked", re.sub(r"^\S+\s*", "", c)
    return "todo", ""


def parse(text: str) -> dict:
    milestones, ms, rc = [], None, None
    decisions = 0
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if m := MS_HEAD.match(line):
            ms = {"n": m[1], "title": m[2].strip(), "rcs": []}
            milestones.append(ms)
        elif (m := RC_HEAD.match(line)) and ms is not None:
            rc = {"id": m[1], "title": m[2].strip(), "tasks": [], "gate": ""}
            ms["rcs"].append(rc)
        elif (m := ROW.match(line)) and rc is not None:
            state, when = status_of(m[3])
            rc["tasks"].append({"id": m[1], "task": inline(m[2]), "state": state,
                                "when": html.escape(when), "notes": inline(m[4])})
        elif (m := GATE.match(line)) and rc is not None and m[1] == rc["id"]:
            body = m[3]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].startswith(("#", "|", "---")):
                body += " " + lines[j].strip()
                j += 1
            rc["gate"] = inline((m[2].strip(" ():") + " " + body).strip())
            rc["gate_passed"] = "passed" in m[2].lower()
        elif DECISION.match(line):
            decisions += 1
    tasks = [t for ms in milestones for rc in ms["rcs"] for t in rc["tasks"]]
    nxt = next((t for t in tasks if t["state"] != "done"), None)
    return {"milestones": milestones, "tasks": tasks, "next": nxt, "decisions": decisions}


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2733;--mute:#5d6b7a;--line:#e1e5ea;--accent:#2f6f8f;
--done:#2f8a5b;--done-bg:#e3f3ea;--now:#c77a2c;--now-bg:#fbeedd;--todo:#8a96a3;--todo-bg:#eef1f4;
--blk:#b23b3b;--blk-bg:#f8e3e3;--code:#eef1f4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121619;--card:#1a1f24;--ink:#e3e8ed;
--mute:#9aa6b2;--line:#2c343c;--accent:#7fbfdc;--done:#5fc28f;--done-bg:#1b3226;--now:#e3a25e;--now-bg:#3a2b1a;
--todo:#8a96a3;--todo-bg:#232a31;--blk:#e77;--blk-bg:#3a1f1f;--code:#262c33}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Segoe UI",system-ui,sans-serif}
main{max-width:1080px;margin:0 auto;padding:28px 16px 80px}
h1{font-size:24px;margin:0 0 4px}
.sub{color:var(--mute);font-size:13px}
.hero{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:20px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.stat b{display:block;font-size:26px;font-variant-numeric:tabular-nums}
.stat span{color:var(--mute);font-size:12px;text-transform:uppercase;letter-spacing:.05em}
.bar{height:8px;border-radius:4px;background:var(--todo-bg);overflow:hidden;display:flex}
.bar i{display:block;height:100%}
.bar .d{background:var(--done)}.bar .n{background:var(--now)}
.next{background:var(--now-bg);border:1px solid var(--now);border-radius:10px;padding:14px 16px;margin:0 0 20px}
.next h2{margin:0 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--now)}
.filters{display:flex;gap:8px;margin:0 0 16px;flex-wrap:wrap}
.filters button{font:inherit;font-size:13px;padding:5px 12px;border-radius:16px;border:1px solid var(--line);
background:var(--card);color:var(--ink);cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
.ms{margin:28px 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
details.rc{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--todo);border-radius:10px;
margin:0 0 12px;overflow:hidden}
details.rc.done{border-left-color:var(--done)}details.rc.now{border-left-color:var(--now)}
summary{list-style:none;cursor:pointer;padding:12px 16px;display:grid;grid-template-columns:1fr 160px;gap:12px;align-items:center}
summary::-webkit-details-marker{display:none}
summary h3{margin:0;font-size:16px}
summary .meta{font-size:12px;color:var(--mute);text-align:right}
summary .bar{margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:14px}
td{padding:9px 16px;border-top:1px solid var(--line);vertical-align:top}
td.id{white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--mute);width:70px}
td.st{width:120px;white-space:nowrap}
td.notes{color:var(--mute);font-size:13px;width:34%}
tr.is-next td{background:var(--now-bg)}
.pill{display:inline-block;font-size:12px;padding:1px 9px;border-radius:10px}
.pill.done{background:var(--done-bg);color:var(--done)}.pill.now{background:var(--now-bg);color:var(--now)}
.pill.todo{background:var(--todo-bg);color:var(--todo)}.pill.blocked{background:var(--blk-bg);color:var(--blk)}
.gate{padding:10px 16px;border-top:1px dashed var(--line);font-size:13px;color:var(--mute)}
.gate strong:first-child{color:var(--ink)}
code{background:var(--code);padding:0 4px;border-radius:3px;font-size:.9em}
a{color:var(--accent)}
.hide{display:none}
@media (max-width:640px){td.notes{display:none}summary{grid-template-columns:1fr}summary .meta{text-align:left}}
"""

JS = """
const btns=document.querySelectorAll('.filters button');
function apply(f){btns.forEach(b=>b.setAttribute('aria-pressed',b.dataset.f===f));
document.querySelectorAll('tr[data-s]').forEach(r=>r.classList.toggle('hide',f!=='all'&&(f==='open')===(r.dataset.s==='done')));
try{localStorage.setItem('tc-filter',f)}catch(e){}}
btns.forEach(b=>b.onclick=()=>apply(b.dataset.f));
let f='all';try{f=localStorage.getItem('tc-filter')||'all'}catch(e){}apply(f);
// keep open/closed panels across the auto-reload
const key='tc-open';let open=[];try{open=JSON.parse(localStorage.getItem(key)||'null')}catch(e){}
document.querySelectorAll('details.rc').forEach(d=>{if(open)d.open=open.includes(d.id);
d.addEventListener('toggle',()=>{try{localStorage.setItem(key,JSON.stringify([...document.querySelectorAll('details.rc[open]')].map(x=>x.id)))}catch(e){}})});
const y=sessionStorage.getItem('tc-y');if(y)scrollTo(0,+y);
setTimeout(()=>{sessionStorage.setItem('tc-y',scrollY);location.reload()},30000);
"""


def bar(done: int, now: int, total: int) -> str:
    total = total or 1
    return (f'<div class="bar"><i class="d" style="width:{100*done/total:.1f}%"></i>'
            f'<i class="n" style="width:{100*now/total:.1f}%"></i></div>')


def render(p: dict) -> str:
    tasks = p["tasks"]
    total = len(tasks)
    done = sum(t["state"] == "done" for t in tasks)
    now = sum(t["state"] == "now" for t in tasks)
    rcs = [rc for ms in p["milestones"] for rc in ms["rcs"]]
    rcs_done = sum(bool(rc["tasks"]) and all(t["state"] == "done" for t in rc["tasks"]) for rc in rcs)
    nxt = p["next"]
    next_rc = next((rc for rc in rcs if nxt and nxt in rc["tasks"]), None)
    built = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    out = [f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Test Console Tracker</title><style>{CSS}</style></head><body><main>
<h1>ISO Rating Test Console</h1>
<div class="sub">Generated from <a href="TC-PLAN.md">docs/TC-PLAN.md</a> at {built} · reloads every 30 s</div>
<div class="hero">
<div class="stat"><span>Tasks done</span><b>{done} / {total}</b>{bar(done, now, total)}</div>
<div class="stat"><span>RCs complete</span><b>{rcs_done} / {len(rcs)}</b>{bar(rcs_done, 0, len(rcs))}</div>
<div class="stat"><span>In progress</span><b>{now}</b></div>
<div class="stat"><span>Decisions recorded</span><b>{p['decisions']}</b></div>
</div>"""]
    if nxt:
        out.append(f'<div class="next"><h2>Next up · {next_rc["id"]} {html.escape(next_rc["title"])}</h2>'
                   f'<strong>{nxt["id"]}</strong> — {nxt["task"]}</div>')
    else:
        out.append('<div class="next"><h2>All tasks done</h2>Every task in the plan is marked ✅.</div>')
    out.append('<div class="filters"><button data-f="all">All</button><button data-f="open">Open</button>'
               '<button data-f="done">Done</button></div>')

    for ms in p["milestones"]:
        out.append(f'<div class="ms">Milestone {ms["n"]} · {html.escape(ms["title"])}</div>')
        for rc in ms["rcs"]:
            ts = rc["tasks"]
            d = sum(t["state"] == "done" for t in ts)
            n = sum(t["state"] == "now" for t in ts)
            cls = "done" if ts and d == len(ts) else ("now" if (n or rc is next_rc) else "todo")
            is_open = " open" if cls == "now" else ""
            out.append(f'<details class="rc {cls}" id="{rc["id"]}"{is_open}><summary><div><h3>{rc["id"]} · '
                       f'{html.escape(rc["title"])}</h3></div><div class="meta">{d} of {len(ts)} done'
                       f'{bar(d, n, len(ts))}</div></summary><table>')
            for t in ts:
                label = {"done": "Done", "now": "In progress", "todo": "To do", "blocked": "Blocked"}[t["state"]]
                when = f' {t["when"]}' if t["when"] else ""
                mark = " is-next" if t is nxt else ""
                out.append(f'<tr class="{mark.strip()}" data-s="{t["state"]}"><td class="id">{t["id"]}</td>'
                           f'<td>{t["task"]}</td><td class="st"><span class="pill {t["state"]}">{label}</span>'
                           f'<div class="sub">{when}</div></td><td class="notes">{t["notes"]}</td></tr>')
            out.append("</table>")
            if rc["gate"]:
                out.append(f'<div class="gate"><strong>Gate{" ✅" if rc.get("gate_passed") else ""}:</strong> '
                           f'{rc["gate"]}</div>')
            out.append("</details>")
    out.append(f"</main><script>{JS}</script></body></html>")
    return "\n".join(out)


def main() -> int:
    if "--hook" in sys.argv:
        try:
            payload = json.load(sys.stdin)
        except Exception:
            return 0
        path = str((payload.get("tool_input") or {}).get("file_path", ""))
        if not path.replace("\\", "/").endswith("docs/TC-PLAN.md"):
            return 0
    OUT.write_text(render(parse(PLAN.read_text(encoding="utf-8"))), encoding="utf-8")
    if "--hook" not in sys.argv:
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
