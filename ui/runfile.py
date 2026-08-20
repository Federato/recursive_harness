"""One standalone HTML file per run, and an index over them.

A run file opens by double-click with no server running, holds everything the
run produced, and can be sent to someone. That is the whole reason it is a file
and not a page: the run store answers *what happened*, and a file answers *here,
look*.

**These files are git-ignored and must stay that way.** A run holds ISO's
licensed premium values, which is the same reason notebook outputs are stripped
before commit. `.gitignore` excludes `results/`; nothing here writes anywhere
else.

### The page, top to bottom

1. **the verdict** -- agree, differ, not applicable, refused, calls
2. **what changed since the last run** of this layer and class
3. **a lead visual, chosen by layer** -- the shape that layer's question has
4. **configuration x jurisdiction** -- the grid
5. **every state, worst first** -- expanding to the fields that differ

**The grid earns its place because a run holds many configurations.** Every
other view organises results by state, which is the wrong axis when the fault
sits in a configuration: ten disagreements scattered across the country read as
ten problems in a state table and as one row here.

### Two rules this module is built around

**Nothing is computed here that is computed elsewhere.** Agreement was decided
by `phase2_compare.compare_payload`, the matrix by `scripts/layers.py`, the
drawings by `ui/charts.py`. A second opinion about what *differ* means, formed
while rendering, is exactly the drift the project keeps one definition to avoid.

**An offline run gets the same page asking a different question** -- not *do we
agree with ISO* but *did our own engine behave sensibly*. It says so in a banner
that cannot be missed, because a full-looking run page with no comparison behind
it reads as a passing run.
"""
from __future__ import annotations

import html
import json
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import charts

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "runs"
INDEX_JSON = RUNS / "index.json"
INDEX_HTML = RUNS / "index.html"

#: Statuses that mean *this rated and ISO disagreed*. One list, because three
#: places ask the question.
FAILING = ("DIFF", "PREMIUM ONLY")

CSS = """
:root{--ink:#1a1d21;--muted:#6b7580;--line:#e3e8ee;--blue:#2b6cb0;
--red:#c0392b;--amber:#b7791f;--grey:#9aa5b1;--green:#2f855a;--bg:#f7f9fb}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{background:#fff;border-bottom:1px solid var(--line);padding:16px 22px}
header h1{font-size:17px;margin:0 0 3px;font-weight:650}
header .sub{color:var(--muted);font-size:12.5px}
main{padding:18px 22px;max-width:1180px}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;
padding:14px 16px;margin-bottom:15px}
.card h2{font-size:12px;text-transform:uppercase;letter-spacing:.05em;
color:var(--muted);margin:0 0 10px;font-weight:650}
.big{font-size:15px;font-weight:650;margin:0 0 4px}
.counts{display:flex;gap:22px;flex-wrap:wrap;margin:8px 0 2px}
.counts div{font-size:12.5px;color:var(--muted)}
.counts b{display:block;font-size:20px;color:var(--ink);
font-variant-numeric:tabular-nums;font-weight:650}
.counts b.bad{color:var(--red)}
.counts b.ok{color:var(--green)}
.banner{background:#eef2f6;border:1px solid #d6dee6;border-left:3px solid var(--grey);
border-radius:6px;padding:12px 15px;margin-bottom:15px;font-size:12.5px}
.banner b{color:var(--ink)}
.chg{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:10px}
.chg > div{border:1px solid var(--line);border-radius:7px;padding:10px 12px}
.chg .k{font-size:11.5px;color:var(--muted)}
.chg .v{font-size:26px;font-weight:650;font-variant-numeric:tabular-nums;
line-height:1.15}
.chg .w{font-size:11.5px;color:var(--muted);margin-top:3px}
.chg .v.bad{color:var(--red)} .chg .v.ok{color:var(--green)}
.chg .v.new{color:var(--blue)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;font-weight:650;color:var(--muted);font-size:11px;
text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--line);
padding:6px 7px}
td{padding:5px 7px;border-bottom:1px solid #f0f3f6;vertical-align:top}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.st{font-weight:650;font-size:11.5px;white-space:nowrap}
.st.MATCH,.st.RATED{color:var(--blue)}
.st.DIFF{color:var(--red)}
.st.PREMIUM{color:var(--amber)}
.st.NOT,.st.BUILD,.st.NA{color:var(--grey)}
.st.ENGINE{color:var(--red)}
.det{color:var(--muted);font-size:11.5px}
details>summary{cursor:pointer;color:var(--blue);font-size:11.5px}
.fields{margin:6px 0 2px;border-left:2px solid var(--line);padding-left:9px}
.fields div{font-size:11.5px;color:var(--muted);
font-family:ui-monospace,Menlo,Consolas,monospace}
.note{font-size:12px;color:var(--muted);border-left:2px solid var(--line);
padding-left:9px;margin-top:7px}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;
background:#eef2f6;color:var(--muted);margin-right:5px}
a{color:var(--blue)}
.scroll{overflow-x:auto}
.matrix{font-size:11.5px}
.matrix th{font-size:10px;padding:4px 2px;text-align:center}
.matrix td{text-align:center;padding:2px;border-bottom:1px solid #f6f8fa}
.matrix td.rowhead,.matrix th.rowhead{text-align:left;white-space:nowrap;
color:var(--ink);font-weight:600;padding-right:10px}
.cell{display:inline-block;width:16px;height:16px;border-radius:3px;
border:0;padding:0;cursor:pointer}
.cell:hover{outline:2px solid var(--ink);outline-offset:1px}
.c-ok{background:#bcd7ef} .c-bad{background:var(--red)}
.c-amb{background:var(--amber)} .c-na{background:#e3e8ee}
.c-moved{background:#7aa9d4} .c-flat{background:#f0d9a8}
.c-err{background:#7b241c}
.legend{font-size:11.5px;color:var(--muted);margin-top:8px;display:flex;
gap:14px;flex-wrap:wrap;align-items:center}
.legend span{display:flex;gap:5px;align-items:center}
.legend i{display:inline-block;width:14px;height:14px;border-radius:3px}
.sortlink{font-size:11.5px;color:var(--blue);cursor:pointer;
text-decoration:underline;margin-left:10px;font-weight:400}
.panel{position:fixed;pointer-events:none;background:#1f2933;color:#fff;
border-radius:6px;padding:8px 11px;font-size:12px;line-height:1.5;z-index:50;
box-shadow:0 6px 20px rgba(0,0,0,.25);display:none;max-width:320px}
.panel .k{color:#9aa5b1}
.filterbar{font-size:12px;margin-bottom:8px;display:none;
background:#eef6ff;border:1px solid #cfe2f5;border-radius:6px;padding:7px 10px}
.filterbar button{margin-left:8px;font-size:11.5px;background:#fff;
border:1px solid #cbd2d9;border-radius:5px;padding:2px 8px;cursor:pointer}
.reviewlink{display:inline-block;margin-top:8px;font-size:12.5px;font-weight:600;
color:var(--blue);text-decoration:none;border:1px solid #cfe2f5;background:#eef6ff;
border-radius:6px;padding:5px 11px}
"""


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def _dec(x):
    try:
        return abs(Decimal(str(x)))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _num(x):
    try:
        return float(str(x))
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------ the lead visual

def _lead(plan: dict, results: list) -> str:
    """The one drawing that answers *this layer's* question.

    Not the same picture for every layer, deliberately. L3 varies a numeric
    limit, so a curve is the shape; L4 varies which of six slots carries a
    deductible, and a line through six unordered slots would invent an ordering
    ISO does not file; L1 and L2 hold one configuration, so the variation is the
    geography and the spread is the chart.
    """
    layer = plan.get("layer")
    if layer == "L3":
        return _lead_curve(results)
    if layer == "L4":
        return _lead_slots(results)
    return _lead_spread(results)


def _lead_curve(results: list) -> tuple:
    series: dict = {}
    for r in results:
        value = (r["scenario"]["config"] or {}).get("occurrence_limit")
        if not value:
            continue
        for row in r.get("rows") or []:
            if row.get("ours") in (None, ""):
                continue
            series.setdefault(row["juris"], []).append(
                {"value": value, "ours": str(row["ours"]),
                 "iso": row.get("iso")})
    return ("Our premium against the each-occurrence limit",
            charts.response_curve("each-occurrence limit", series),
            "The premium should rise with the limit, smoothly, in every "
            "jurisdiction. <b>A kink, a flat run or a step usually means a "
            "lookup missed and something fell back</b> — and that is legible "
            "with or without ISO's answer.")


def _lead_slots(results: list) -> tuple:
    items = []
    for r in results:
        cfg = r["scenario"]["config"] or {}
        slot = next((k for k in cfg if k.endswith("deductible")), None)
        if not slot:
            continue
        pcts, moved = [], 0
        for row in r.get("rows") or []:
            base, ours = _num(row.get("base")), _num(row.get("ours"))
            if not base or ours is None:
                continue
            pcts.append((ours - base) / base * 100.0)
            if ours != base:
                moved += 1
        items.append({
            # ISO's own wording, taken from the scenario's description rather
            # than prettified from the control id -- `prods_bipd_deductible`
            # cleaned up by hand reads "prods bipd", which is nobody's name for
            # anything.
            "label": r["scenario"]["describes"].split("=")[0].strip(),
            "pct": sum(pcts) / len(pcts) if pcts else 0.0,
            "states": len(pcts), "moved_in": moved,
        })
    return ("How far each deductible slot moved the premium",
            charts.slot_bars(items),
            "The question this layer asks is <b>is any slot ignored</b>. A slot "
            "that moved nothing in any jurisdiction is either a fact about "
            "ISO's filing or a deductible we never applied — and "
            "<code>probe_no_op</code> is what tells those apart.")


def _lead_spread(results: list) -> tuple:
    points = []
    for r in results:
        for row in r.get("rows") or []:
            if row.get("ours") not in (None, ""):
                points.append({"juris": row["juris"], "ours": str(row["ours"]),
                               "iso": row.get("iso"), "status": row.get("status")})
    return ("Premium by jurisdiction",
            charts.premium_spread(points),
            "One configuration in every jurisdiction, so the variation is the "
            "geography. A class costing more in some states than others is what "
            "a loss cost is; <b>what is worth looking at is the tail</b>, where "
            "a state far outside the rest is either a real filed difference or "
            "our bug.")


# ------------------------------------------------------- what changed since

def _states_failing(results: list) -> dict:
    """`{juris: worst status}` for every jurisdiction that failed in this run."""
    out = {}
    for r in results:
        for row in r.get("rows") or []:
            if row.get("status") in FAILING:
                out[row["juris"]] = row["status"]
    return out


def _states_seen(results: list) -> set:
    return {row["juris"] for r in results for row in (r.get("rows") or [])}


def _previous(plan: dict) -> dict | None:
    """The last run file of this layer and class, from the index.

    Read from the index rather than the run store because the store holds one
    line per *scenario* and a run is the whole set of them; the index is where
    a run exists as one thing.
    """
    want_layer, want_class = plan.get("layer"), plan.get("class_code") or ""
    prior = [e for e in entries()
             if e.get("layer") == want_layer
             and (e.get("class_code") or "") == want_class]
    return prior[-1] if prior else None


def _refusing(results: list) -> dict:
    """`{juris: status}` for anything the engine would not complete."""
    out = {}
    for r in results:
        for row in r.get("rows") or []:
            if row.get("status") in ("ENGINE STOPPED", "ENGINE ERROR",
                                     "BUILD ERROR"):
                out[row["juris"]] = row["status"]
    return out


def _premiums(results: list) -> dict:
    """`{"<configuration>|<state>": premium}` for everything that rated.

    Keyed by the configuration's own description rather than its position,
    because position changes the moment an allowance thins the list differently
    and a comparison keyed on it would silently compare two different things.
    """
    out = {}
    for r in results:
        cfg = r["scenario"]["describes"]
        for row in r.get("rows") or []:
            if row.get("ours") not in (None, ""):
                out[f"{cfg}|{row['juris']}"] = str(row["ours"])
    return out


def change_counts(plan: dict, results: list) -> dict | None:
    """What changed since the last run of this layer and class, as data.

    **One computation, two readers** -- the run file renders it and the `/tests`
    page shows it the moment a run finishes. Two implementations of *what
    changed* would eventually disagree, and the day they did there would be no
    way to tell which was right.

    Returns `None` when there is nothing to compare against, which the callers
    must show as *first run* rather than as four zeros.

    **Live runs are compared by jurisdiction.** A state that was failing and is
    not failing now counts. That is looser than *the same configuration was
    re-run and passed*, and the label says so: `no longer failing`, never
    *fixed*. A state can stop failing because the configuration that broke it
    was not repeated, and nothing here may claim a fix it did not measure.

    **Offline runs are compared against themselves**, because there is no ISO
    answer on either side: did the engine start or stop refusing, and did a
    premium move when no rule changed. The second is a regression and costs
    nothing to find.
    """
    prev = _previous(plan)
    if not prev:
        return None
    seen_now = _states_seen(results)
    newly_covered = sorted(seen_now - set(prev.get("seen") or []))
    cfgs_now = {r["scenario"]["describes"] for r in results}
    new_cfgs = sorted(cfgs_now - set(prev.get("configs") or []))
    common = {
        "against": prev.get("file"), "at": prev.get("at"),
        "newly_covered": newly_covered, "new_configs": new_cfgs,
    }

    if plan.get("offline") or prev.get("offline"):
        now_ref, was_ref = set(_refusing(results)), set(prev.get("refusing") or [])
        now_p, was_p = _premiums(results), prev.get("premiums") or {}
        shared = sorted(set(now_p) & set(was_p))
        moved = [k for k in shared if now_p[k] != was_p[k]]
        return {**common, "mode": "offline",
                "newly_refusing": sorted(now_ref - was_ref),
                "no_longer_refusing": sorted(was_ref - now_ref),
                "premium_changed": [m.split("|")[-1] for m in moved],
                "compared_pairs": len(shared)}

    now_bad = set(_states_failing(results))
    was_bad = set(prev.get("failing") or [])
    return {**common, "mode": "live",
            "new_problems": sorted(now_bad - was_bad),
            "no_longer_failing": sorted(was_bad - now_bad),
            "still_failing": sorted(now_bad & was_bad)}


def _box(k, v, cls, w) -> str:
    return (f'<div><div class="k">{_e(k)}</div>'
            f'<div class="v {cls}">{_e(v)}</div>'
            f'<div class="w">{_e(w)}</div></div>')


def _changed(plan: dict, results: list) -> str:
    """The block under the verdict, rendered from `change_counts`."""
    c = change_counts(plan, results)
    if c is None:
        return ('<div class="card"><h2>What changed since last run</h2>'
                '<div class="note">This is the first recorded run of '
                f'{_e(plan.get("layer"))}'
                + (f' for class {_e(plan.get("class_code"))}'
                   if plan.get("class_code") else "")
                + '. There is nothing to compare it with, which is why no '
                  'counts are shown rather than four zeros.</div></div>')

    covered = (f"+{len(c['newly_covered'])}" if c["newly_covered"]
               else (f"{len(c['new_configs'])} new configurations"
                     if c["new_configs"] else "0"))
    covered_w = (", ".join(c["newly_covered"][:6])
                 or (", ".join(c["new_configs"][:2]) if c["new_configs"]
                     else "nothing new"))

    if c["mode"] == "offline":
        boxes = (
            _box("Newly refusing", len(c["newly_refusing"]), "bad",
                 ", ".join(c["newly_refusing"][:6]) or "none")
            + _box("No longer refusing", len(c["no_longer_refusing"]), "ok",
                   ", ".join(c["no_longer_refusing"][:6]) or "none")
            + _box("Premium changed", len(c["premium_changed"]),
                   "bad" if c["premium_changed"] else "",
                   ", ".join(c["premium_changed"][:6]) or "none")
            + _box("Newly covered", covered, "new", covered_w))
        why = (f'Compared against <b>{_e(c["against"])}</b> across the '
               f'{c["compared_pairs"]} configuration-and-state pairs both runs '
               f'hold. <b>A premium that moved when no rule changed is a '
               f'regression</b>, and finding it cost nothing.')
    else:
        boxes = (
            _box("New problems", len(c["new_problems"]), "bad",
                 ", ".join(c["new_problems"][:6]) or "none")
            + _box("No longer failing", len(c["no_longer_failing"]), "ok",
                   ", ".join(c["no_longer_failing"][:6]) or "none")
            + _box("Still failing", len(c["still_failing"]), "",
                   ", ".join(c["still_failing"][:6]) or "none")
            + _box("Newly covered", covered, "new", covered_w))
        why = (f'Compared by jurisdiction against <b>{_e(c["against"])}</b>. '
               f'<b>No longer failing is not the same as fixed</b>: a state can '
               f'stop failing because the configuration that broke it was not '
               f'repeated, so this block reports what it measured and not what '
               f'it hopes.')

    return ('<div class="card"><h2>What changed since '
            f'{_e((c.get("at") or "")[:10])}</h2>'
            f'<div class="chg">{boxes}</div>'
            f'<div class="note">{why} Computed when this file was written and '
            f'frozen into it.</div></div>')


# -------------------------------------------------------------- the verdict

def _verdict(plan: dict, results: list) -> str:
    roll = plan.get("rollup") or {}
    offline = bool(plan.get("offline"))
    disagree = roll.get("differ", 0) + roll.get("premium_only", 0)
    if offline:
        unmoved = sum(len((r["summary"].get("unmoved") or [])) for r in results)
        return (
            '<div class="card">'
            f'<p class="big">{_e(roll.get("rated", 0))} rated · '
            f'{_e(roll.get("not_applicable", 0))} not applicable · '
            f'{_e(roll.get("engine_stopped", 0))} refused</p>'
            '<div class="counts">'
            f'<div><b>{_e(roll.get("scenarios", 0))}</b>scenarios</div>'
            f'<div><b class="ok">{_e(roll.get("rated", 0))}</b>rated cleanly</div>'
            f'<div><b>{_e(roll.get("not_applicable", 0))}</b>not applicable</div>'
            f'<div><b>{_e(roll.get("engine_stopped", 0))}</b>engine refused</div>'
            f'<div><b>0</b>ISO calls</div>'
            f'<div><b class="{"bad" if unmoved else ""}">{unmoved}</b>'
            f'did not move the premium</div>'
            '</div>'
            '<div class="note">Not applicable is a third outcome and never a '
            'failure. <b>Did not move the premium</b> is the offline run\'s '
            'finding: a configuration that rated and changed nothing exercised '
            'nothing, and <code>probe_no_op</code> says whether that is ISO\'s '
            'filing or our chosen value.</div></div>')
    return (
        '<div class="card">'
        f'<p class="big">{_e(roll.get("agree", 0))} agree · {disagree} differ · '
        f'{_e(roll.get("not_applicable", 0))} not applicable</p>'
        '<div class="counts">'
        f'<div><b>{_e(roll.get("scenarios", 0))}</b>scenarios</div>'
        f'<div><b class="ok">{_e(roll.get("agree", 0))}</b>agree with ISO</div>'
        f'<div><b class="{"bad" if disagree else ""}">{disagree}</b>disagree</div>'
        f'<div><b>{_e(roll.get("not_applicable", 0))}</b>not applicable</div>'
        f'<div><b>{_e(roll.get("engine_stopped", 0))}</b>engine refused</div>'
        f'<div><b>{_e(roll.get("live_calls", 0))}</b>ISO calls</div>'
        '</div>'
        '<div class="note">Not applicable is a third outcome and never a '
        'failure: the jurisdiction does not declare that configuration legal. '
        'Premium only means the premium agreed and an underlying field did '
        'not.</div></div>')


def _banner(plan: dict) -> str:
    if not plan.get("offline"):
        return ""
    return ('<div class="banner"><b>No ISO comparison.</b> This run rated '
            'through our engine only — 0 live calls. <b>Nothing here says '
            'whether a premium is right</b>; agreement is decided by ISO\'s '
            'answer and this run did not ask for one. What it does say is '
            'whether every configuration built, rated, and moved the premium '
            'the way the filed tables imply.</div>')


# --------------------------------------------------------------- the matrix

def _cell_class(row: dict, offline: bool) -> str:
    status = row.get("status") or ""
    if status in ("NOT APPLICABLE",):
        return "c-na"
    if status in ("BUILD ERROR", "ENGINE ERROR", "RAAS FAILED", "ENGINE STOPPED"):
        return "c-err"
    if offline:
        if row.get("moved") is False:
            return "c-flat"
        return "c-moved"
    if status == "DIFF":
        return "c-bad"
    if status == "PREMIUM ONLY":
        return "c-amb"
    return "c-ok"


def _matrix_data(plan: dict, results: list) -> list:
    offline = bool(plan.get("offline"))
    out = []
    for i, r in enumerate(results):
        for row in r.get("rows") or []:
            out.append({
                "ci": i, "cfg": r["scenario"]["describes"], "st": row["juris"],
                "k": _cell_class(row, offline),
                "status": row.get("status") or "",
                "ours": row.get("ours"), "iso": row.get("iso"),
                "delta": row.get("delta"),
                "detail": (row.get("detail") or "")[:160],
                "resolved": row.get("resolved") or {},
                "moved": row.get("moved"),
            })
    return out


def _matrix(plan: dict, results: list) -> str:
    offline = bool(plan.get("offline"))
    legend = ([('c-moved', 'rated, premium moved'),
               ('c-flat', 'rated, premium unchanged'),
               ('c-na', 'not applicable'), ('c-err', 'refused or failed')]
              if offline else
              [('c-ok', 'agrees'), ('c-amb', 'premium only'),
               ('c-bad', 'differs'), ('c-na', 'not applicable'),
               ('c-err', 'refused or failed')])
    return (
        '<div class="card"><h2>Configuration × jurisdiction'
        '<span class="sortlink" id="sorter">sort states by problems ▸</span>'
        '</h2>'
        '<div class="scroll"><table class="matrix" id="matrix"></table></div>'
        '<div class="legend">'
        + "".join(f'<span><i class="{k}"></i> {v}</span>' for k, v in legend)
        + '<span class="det">— hover for detail, click to filter the table'
          '</span></div>'
        '<div class="note"><b>A run holds many configurations, and the fault is '
        'often in one of them.</b> Read down a row: disagreements scattered '
        'across the country in a single configuration are one problem, not '
        'twenty.</div></div>')


# ---------------------------------------------------------- the state table

def _sort_key(row: dict):
    """Biggest disagreement first, then everything that rated, then the rest.

    A run is read to find what is wrong with it. Sorting alphabetically puts
    Alabama at the top of a page whose point is Louisiana.
    """
    status = row.get("status") or ""
    d = _dec(row.get("delta"))
    if status == "DIFF":
        return (0, -(d or Decimal(0)), row.get("st", ""))
    if status == "PREMIUM ONLY":
        return (1, Decimal(0), row.get("st", ""))
    if status in ("MATCH", "RATED"):
        return (2, Decimal(0), row.get("st", ""))
    return (3, Decimal(0), row.get("st", ""))


def _table(plan: dict, results: list) -> str:
    offline = bool(plan.get("offline"))
    rows = []
    for i, r in enumerate(results):
        for row in r.get("rows") or []:
            rows.append({**row, "st": row["juris"], "ci": i,
                         "cfg": r["scenario"]["describes"]})
    head = ("<tr><th>State<th>Configuration<th>Status<th class=n>Ours"
            + ("<th class=n>From base" if offline
               else "<th class=n>ISO<th class=n>Difference")
            + "<th>What differs</tr>")
    out = []
    for r in sorted(rows, key=_sort_key):
        status = r.get("status") or ""
        cls = status.split(" ")[0]
        diffs = r.get("differences") or []
        cell = ""
        if diffs:
            shown = "".join(
                f"<div>{_e(d.get('field'))}: ours {_e(d.get('ours'))} "
                f"&middot; ISO {_e(d.get('iso'))}</div>" for d in diffs)
            cell = (f"<details><summary>{len(diffs)} field"
                    f"{'s' if len(diffs) != 1 else ''}</summary>"
                    f"<div class=fields>{shown}</div></details>")
        elif r.get("detail"):
            cell = f"<span class=det>{_e(r['detail'])}</span>"
        elif offline and r.get("moved") is False:
            cell = ('<span class=det>premium unchanged from the unvaried '
                    'base</span>')
        extra = "".join(f"<span class=tag>{_e(k)} = {_e(v)}</span>"
                        for k, v in (r.get("resolved") or {}).items())
        out.append(
            f"<tr id='r-{_e(r['st'])}-{r['ci']}'><td><b>{_e(r.get('juris'))}</b>"
            + ("<br>" + extra if extra else "")
            + f"<td class=det>{_e(r['cfg'])}"
            + f"<td class='st {_e(cls)}'>{_e(status)}"
            + f"<td class=n>{_e(r.get('ours', '--'))}"
            + (f"<td class=n>{_e(r.get('from_base', ''))}" if offline
               else f"<td class=n>{_e(r.get('iso', '--'))}"
                    f"<td class=n>{_e(r.get('delta', ''))}")
            + f"<td>{cell}</tr>")
    return ('<div class="card"><h2>Every state, worst first</h2>'
            '<div class="filterbar" id="fbar"></div>'
            '<div class="scroll"><table id="statetable">' + head
            + "".join(out) + "</table></div></div>")


# ------------------------------------------------------------ what ran card

def _matrix_card(plan: dict, results: list) -> str:
    t = plan.get("thinning") or {}
    bits = []
    if plan.get("class_code"):
        bits.append(f"<div>Class <b>{_e(plan['class_code'])}</b>, "
                    f"exposure <b>{_e(plan.get('exposure'))}</b></div>")
    for g in plan.get("groups") or []:
        if g.get("basis"):
            bits.append(f"<div>Premium basis <b>{_e(g['basis'])}</b> in "
                        f"{len(g['jurisdictions'])} jurisdictions</div>")
    if plan.get("undeclared"):
        bits.append(
            f"<div><b>Not filed</b> in {len(plan['undeclared'])}: "
            f"{_e(' '.join(plan['undeclared']))}"
            f"<div class=note>ISO declares no premium basis for this class "
            f"there. That is a fact about coverage, not a failure, and it is "
            f"reported rather than filtered out.</div></div>")
    if t.get("applied"):
        bits.append(
            f"<div><b>Thinned to fit an allowance of {_e(t['allowance'])} "
            f"live calls</b>: {_e(t['configs_kept'])} of "
            f"{_e(t['configs_planned'])} configurations kept, every "
            f"jurisdiction kept."
            f"<div class=note>{_e(t.get('why', ''))}. Dropped: "
            f"{_e('; '.join(t.get('dropped') or []))}</div></div>")
    else:
        bits.append(f"<div>The full matrix ran: "
                    f"{_e(plan.get('configs_planned'))} configuration(s), "
                    f"no thinning.</div>")
    missed = []
    for r in results:
        s = r.get("summary") or {}
        if s.get("not_reached"):
            missed.append(f"{r['scenario']['describes']}: "
                          + " ".join(s["not_reached"]))
    if plan.get("stopped_after") is not None or missed:
        detail = ""
        if plan.get("stopped_after") is not None:
            detail = (f" after {_e(plan['stopped_after'])} of "
                      f"{len(plan.get('scenarios') or [])} scenarios")
        bits.append(
            f"<div><b>Stopped early</b>{detail}. What follows is a partial run."
            + ("<div class=note>Never reached &mdash; "
               + "; ".join(_e(m) for m in missed) + "</div>" if missed else "")
            + "<div class=note>A stopped run is not a failed run, and the "
              "states it never reached are named here so its coverage is not "
              "read as complete.</div></div>")
    return ("<div class=card><h2>What actually ran</h2>"
            + "".join(bits) + "</div>")


# ------------------------------------------------------------------- writing

def write_run(plan: dict, results: list, engine_version: str = "") -> Path:
    """Write one run file. Returns its path.

    `results` is `scripts.layers.run`'s per-scenario output: each carries the
    scenario, the stored summary and the rows.
    """
    RUNS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    who = plan.get("class_code") or "base"
    name = f"{plan.get('layer', 'L')}-{who}-{stamp}.html"
    roll = plan.get("rollup") or {}
    offline = bool(plan.get("offline"))
    disagree = roll.get("differ", 0) + roll.get("premium_only", 0)

    lead_title, lead_svg, lead_note = _lead(plan, results)
    title = (f"{plan.get('layer')} {plan.get('name')}"
             + (f" &middot; class {_e(plan.get('class_code'))}"
                if plan.get("class_code") else ""))

    body = [
        "<header>",
        f"<h1>{title}</h1>",
        f"<div class=sub>{_e(plan.get('what'))} &middot; "
        f"{time.strftime('%d %B %Y, %H:%M')} &middot; engine "
        f"{_e(engine_version) or 'unversioned'} &middot; as-of "
        f"{_e(plan.get('asof'))}"
        + (" &middot; <b>offline</b>" if offline else "") + "</div>",
        f'<a class="reviewlink" href="/review/{name}">Review this run &rarr;</a>',
        "</header><main>",
        _banner(plan),
        _verdict(plan, results),
        _changed(plan, results),
        f'<div class="card"><h2>{_e(lead_title)}</h2>{lead_svg}'
        f'<div class="note">{lead_note}</div></div>',
        _matrix_card(plan, results),
        _matrix(plan, results),
        _table(plan, results),
        "</main>",
        '<div class="panel" id="panel"></div>',
        "<script>" + _SCRIPT.replace(
            "__DATA__", json.dumps(_matrix_data(plan, results), default=str))
        .replace("__OFFLINE__", "true" if offline else "false") + "</script>",
    ]

    doc = (f"<!doctype html><html><head><meta charset=utf-8>"
           f"<title>{plan.get('layer')} {plan.get('name')} "
           f"{plan.get('class_code') or ''} {stamp}</title>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<style>{CSS}</style></head><body>"
           + "".join(body) + "</body></html>")

    path = RUNS / name
    path.write_text(doc, encoding="utf-8")
    _index_append({
        "file": name,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "layer": plan.get("layer"),
        "name": plan.get("name"),
        "class_code": plan.get("class_code"),
        "exposure": plan.get("exposure"),
        "offline": offline,
        "rated": roll.get("rated", 0),
        "agree": roll.get("agree", 0),
        "differ": disagree,
        "live_calls": roll.get("live_calls", 0),
        "partial": plan.get("stopped_after") is not None,
        "run_ids": plan.get("run_ids") or [],
        # What the next run of this layer and class compares itself against.
        # Stored here rather than recomputed from the store because a run is one
        # thing in the index and many lines in the store.
        "failing": sorted(_states_failing(results)),
        "refusing": sorted(_refusing(results)),
        "seen": sorted(_states_seen(results)),
        "configs": sorted({r["scenario"]["describes"] for r in results}),
        "premiums": _premiums(results),
    })
    return path


#: The matrix behaviour. Inline, because a run file has to work from disk with
#: no server -- and because the alternative was a grid you could look at and
#: not interrogate.
_SCRIPT = r"""
const CELLS = __DATA__, OFFLINE = __OFFLINE__;
const STATES = [...new Set(CELLS.map(c => c.st))];
const CONFIGS = [];
CELLS.forEach(c => { if (!CONFIGS[c.ci]) CONFIGS[c.ci] = c.cfg; });
let ORDER = STATES.slice(), FILTER = null, SORTED = false;

function problems(st){
  return CELLS.filter(c => c.st === st &&
    (OFFLINE ? (c.k === 'c-flat' || c.k === 'c-err')
             : (c.k === 'c-bad' || c.k === 'c-amb' || c.k === 'c-err'))).length;
}
function drawMatrix(){
  let h = '<tr><th class="rowhead">Configuration</th>'
        + ORDER.map(s => '<th>' + s + '</th>').join('') + '</tr>';
  CONFIGS.forEach((cfg, ci) => {
    h += '<tr><td class="rowhead">' + cfg + '</td>';
    ORDER.forEach(st => {
      const c = CELLS.find(x => x.ci === ci && x.st === st);
      h += c ? ('<td><button class="cell ' + c.k + '" data-ci="' + ci
                + '" data-st="' + st + '"></button></td>')
             : '<td></td>';
    });
    h += '</tr>';
  });
  const m = document.getElementById('matrix');
  m.innerHTML = h;
  m.querySelectorAll('.cell').forEach(el => {
    el.onmouseenter = ev => showPanel(ev, el);
    el.onmousemove = movePanel;
    el.onmouseleave = hidePanel;
    el.onclick = () => { FILTER = +el.dataset.ci; applyFilter();
      const row = document.getElementById('r-' + el.dataset.st + '-' + el.dataset.ci);
      if (row) row.scrollIntoView({block: 'center'});
    };
  });
}
function showPanel(ev, el){
  const c = CELLS.find(x => x.ci === +el.dataset.ci && x.st === el.dataset.st);
  const p = document.getElementById('panel');
  let h = '<b>' + c.st + ' · ' + c.cfg + '</b><br><span class="k">status</span> '
        + c.status;
  if (c.ours) h += '<br><span class="k">ours</span> ' + c.ours
    + (c.iso ? ' · <span class="k">ISO</span> ' + c.iso : '')
    + (c.delta && c.delta !== '0' ? ' · <b>' + c.delta + '</b>' : '');
  if (OFFLINE && c.moved === false) h += '<br><span class="k">premium unchanged from the base</span>';
  Object.entries(c.resolved || {}).forEach(([k, v]) =>
    h += '<br><span class="k">' + k + '</span> ' + v);
  if (c.detail) h += '<br><span class="k">' + c.detail + '</span>';
  p.innerHTML = h; p.style.display = 'block'; movePanel(ev);
}
function movePanel(ev){
  const p = document.getElementById('panel');
  p.style.left = Math.min(ev.clientX + 14, innerWidth - 340) + 'px';
  p.style.top = Math.min(ev.clientY + 16, innerHeight - 120) + 'px';
}
function hidePanel(){ document.getElementById('panel').style.display = 'none'; }

function applyFilter(){
  const fb = document.getElementById('fbar');
  document.querySelectorAll('#statetable tr[id]').forEach(tr => {
    const ci = +tr.id.split('-').pop();
    tr.style.display = (FILTER === null || ci === FILTER) ? '' : 'none';
  });
  if (FILTER === null) { fb.style.display = 'none'; return; }
  fb.style.display = 'block';
  fb.innerHTML = 'Showing <b>' + CONFIGS[FILTER] + '</b> only'
    + '<button id="clearf">show every configuration</button>';
  document.getElementById('clearf').onclick = () => { FILTER = null; applyFilter(); };
}
document.getElementById('sorter').onclick = () => {
  SORTED = !SORTED;
  ORDER = SORTED
    ? STATES.slice().sort((a, b) => problems(b) - problems(a) || a.localeCompare(b))
    : STATES.slice();
  document.getElementById('sorter').textContent =
    SORTED ? 'back to alphabetical ▸' : 'sort states by problems ▸';
  drawMatrix();
};
drawMatrix();
"""


def _index_append(entry: dict) -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    have = entries()
    have.append(entry)
    INDEX_JSON.write_text(json.dumps(have, indent=1), encoding="utf-8")
    write_index(have)


def entries() -> list:
    if not INDEX_JSON.exists():
        return []
    try:
        return json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    except ValueError:
        return []


def write_index(have: list | None = None) -> Path:
    """Rebuild the index page. Newest first, and it says what each run asked."""
    have = entries() if have is None else have
    rows = []
    for e in sorted(have, key=lambda x: x.get("at", ""), reverse=True):
        rows.append(
            f"<tr><td class=det>{_e(e.get('at'))}"
            f"<td><a href='{_e(e.get('file'))}'>{_e(e.get('layer'))} "
            f"{_e(e.get('name'))}</a>"
            + ("<span class=tag>partial</span>" if e.get("partial") else "")
            + ("<span class=tag>offline</span>" if e.get("offline") else "")
            + f"<td>{_e(e.get('class_code') or '--')}"
            f"<td class=n>{_e(e.get('rated', 0))}"
            f"<td class=n>{_e(e.get('agree', 0))}"
            f"<td class=n>{_e(e.get('differ', 0))}"
            f"<td class=n>{_e(e.get('live_calls', 0))}</tr>")
    doc = (f"<!doctype html><html><head><meta charset=utf-8>"
           f"<title>Harness runs</title>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<style>{CSS}</style></head><body>"
           f"<header><h1>Harness runs</h1>"
           f"<div class=sub>{len(have)} run(s). Every file is self-contained "
           f"and holds ISO's licensed values, which is why none of this is "
           f"committed.</div></header><main><div class=card>"
           f"<div class=scroll><table>"
           f"<tr><th>When<th>Run<th>Class<th class=n>Rated<th class=n>Agree"
           f"<th class=n>Differ<th class=n>ISO calls</tr>"
           + "".join(rows) + "</table></div></div></main></body></html>")
    RUNS.mkdir(parents=True, exist_ok=True)
    INDEX_HTML.write_text(doc, encoding="utf-8")
    return INDEX_HTML
