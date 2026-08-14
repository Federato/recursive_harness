"""Charts as inline SVG strings. No chart library, no build step.

The engine has **no third-party dependency** and a visualization is not a good
enough reason to introduce the first one, or a JavaScript toolchain to a project
whose interface is one HTML string. Four charts, each answering one question:

* `coverage_grid`  -- **which controls have ever been exercised where.** The
  honest answer to *how narrow is the claim*, and the only chart here that is
  interesting when it is empty
* `agreement_over_time` -- agreement per run, oldest first, so a regression is
  visible in the run it appears
* `response_curve`  -- premium against the value that was varied, every
  jurisdiction overlaid; a curve that kinks alone is a defect you can see
  before you can explain
* `status_bars`     -- one run's outcomes, with *not applicable* kept visually
  distinct from *disagrees*, because conflating them is this tool's easiest lie

Colours are stated once. Agreement is blue rather than green: **green reads as
"good" and a match is not a virtue, it is the expected case** -- what deserves
attention is grey (nothing asked) and amber (nothing moved).
"""
from __future__ import annotations

from html import escape

INK = "#1a1d21"
MUTED = "#6b7580"
GRID = "#e3e8ee"
BLUE = "#2b6cb0"          # agrees
RED = "#c0392b"           # differs / refused
AMBER = "#b7791f"         # rated but the premium never moved
GREY = "#9aa5b1"          # not applicable -- never asked
FONT = ("font-family:ui-sans-serif,-apple-system,Segoe UI,Roboto,"
        "Helvetica,Arial,sans-serif")


def _svg(w, h, body, title=""):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" '
            f'role="img" style="{FONT};overflow:visible">'
            + (f"<title>{escape(title)}</title>" if title else "")
            + body + "</svg>")


def _t(x, y, s, size=11, fill=MUTED, anchor="start", weight="400"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>')


def empty(message: str, h: int = 90) -> str:
    """An empty chart says what would fill it. A blank box says nothing."""
    return _svg(600, h,
                f'<rect x="0" y="0" width="600" height="{h}" fill="none" '
                f'stroke="{GRID}" stroke-dasharray="3 3"/>'
                + _t(300, h / 2 + 4, message, 12, MUTED, "middle"))


# --------------------------------------------------------------------- grid

def coverage_grid(controls: list, jurisdictions: list, rated: dict,
                  declined: dict) -> str:
    """Controls down, jurisdictions across. Filled = rated there at least once.

    `rated` and `declined` are `{control_id: [juris]}`. A jurisdiction that
    declined is drawn hollow rather than blank: *asked and not declarable* is a
    different fact from *never asked*, and the difference is the point.
    """
    if not controls or not jurisdictions:
        return empty("no runs stored yet -- this fills in as configurations run")
    cw, rh = 15, 17
    left, top = 190, 40
    w = left + cw * len(jurisdictions) + 12
    h = top + rh * len(controls) + 14
    out = []
    for i, j in enumerate(jurisdictions):
        x = left + i * cw + cw / 2
        out.append(f'<g transform="translate({x:.1f},{top - 6}) rotate(-90)">'
                   + _t(0, 4, j, 9, MUTED, "start") + "</g>")
    for r, c in enumerate(controls):
        y = top + r * rh
        done = set(rated.get(c["id"], []))
        said_no = set(declined.get(c["id"], []))
        out.append(_t(left - 8, y + rh / 2 + 3, c["label"], 10.5,
                      INK if done else MUTED, "end"))
        for i, j in enumerate(jurisdictions):
            x = left + i * cw
            if j in done:
                fill, stroke = BLUE, BLUE
            elif j in said_no:
                fill, stroke = "none", GREY
            else:
                fill, stroke = "none", GRID
            out.append(f'<rect x="{x + 1.5}" y="{y + 2.5}" width="{cw - 3}" '
                       f'height="{rh - 5}" fill="{fill}" stroke="{stroke}" '
                       f'rx="2"><title>{escape(c["label"])} in {escape(j)}: '
                       f'{"rated" if j in done else ("not declarable here" if j in said_no else "never run")}'
                       f'</title></rect>')
        out.append(_t(left + cw * len(jurisdictions) + 6, y + rh / 2 + 3,
                      f"{len(done)}", 10, MUTED))
    return _svg(w, h, "".join(out), "Coverage: controls by jurisdiction")


# ----------------------------------------------------------------- over time

def agreement_over_time(series: list) -> str:
    """Agreement per run, oldest first. Bars, because runs are discrete."""
    series = [s for s in series if s.get("compared")]
    if not series:
        return empty("no ISO-compared runs stored yet")
    w, h = 620, 150
    pad_l, pad_b, pad_t = 34, 34, 12
    n = len(series)
    bw = max(4.0, min(26.0, (w - pad_l - 10) / n - 4))
    step = (w - pad_l - 10) / n
    top = max((s["rated"] or 1) for s in series)
    out = [f'<line x1="{pad_l}" y1="{h - pad_b}" x2="{w - 6}" '
           f'y2="{h - pad_b}" stroke="{GRID}"/>']
    out.append(_t(pad_l - 6, pad_t + 8, str(top), 10, MUTED, "end"))
    for i, s in enumerate(series):
        x = pad_l + i * step + (step - bw) / 2
        scale = (h - pad_b - pad_t) / top
        agree_h = s["agree"] * scale
        bad_h = (s["rated"] - s["agree"]) * scale
        y_agree = h - pad_b - agree_h
        out.append(f'<rect x="{x:.1f}" y="{y_agree:.1f}" width="{bw:.1f}" '
                   f'height="{agree_h:.1f}" fill="{BLUE}" rx="1">'
                   f'<title>{escape(s["at_iso"])} — {s["agree"]} of '
                   f'{s["rated"]} agree — {escape(s["describes"][:70])}</title>'
                   f'</rect>')
        if bad_h > 0:
            out.append(f'<rect x="{x:.1f}" y="{y_agree - bad_h:.1f}" '
                       f'width="{bw:.1f}" height="{bad_h:.1f}" fill="{RED}" '
                       f'rx="1"><title>{s["rated"] - s["agree"]} not '
                       f'agreeing</title></rect>')
        if n <= 14:
            out.append(f'<g transform="translate({x + bw / 2:.1f},'
                       f'{h - pad_b + 6}) rotate(-40)">'
                       + _t(0, 0, s["at_iso"][5:16], 8.5, MUTED, "end") + "</g>")
    return _svg(w, h, "".join(out), "Agreement with ISO, run by run")


# -------------------------------------------------------------------- curve

def response_curve(control_label: str, series: dict, max_states: int = 12) -> str:
    """Premium against the varied value, one line per jurisdiction."""
    series = {j: pts for j, pts in series.items() if len(pts) >= 2}
    if not series:
        return empty("run the same control at two or more values to draw a curve")
    xs = []
    for pts in series.values():
        for p in pts:
            if p["value"] not in xs:
                xs.append(p["value"])
    xs.sort()
    w, h = 620, 210
    pad_l, pad_r, pad_b, pad_t = 56, 74, 46, 12
    prem = [float(p["ours"]) for pts in series.values() for p in pts]
    lo, hi = min(prem), max(prem)
    if hi == lo:
        hi = lo + 1
    def X(v):
        i = xs.index(v)
        return pad_l + (i * (w - pad_l - pad_r) / max(1, len(xs) - 1))
    def Y(p):
        return h - pad_b - (p - lo) * (h - pad_b - pad_t) / (hi - lo)

    out = [f'<line x1="{pad_l}" y1="{h - pad_b}" x2="{w - pad_r}" '
           f'y2="{h - pad_b}" stroke="{GRID}"/>',
           f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{h - pad_b}" '
           f'stroke="{GRID}"/>',
           _t(pad_l - 6, pad_t + 8, f"{hi:,.0f}", 9.5, MUTED, "end"),
           _t(pad_l - 6, h - pad_b, f"{lo:,.0f}", 9.5, MUTED, "end")]
    for v in xs:
        out.append(f'<g transform="translate({X(v):.1f},{h - pad_b + 8}) '
                   f'rotate(-35)">' + _t(0, 0, str(v)[:16], 9, MUTED, "end")
                   + "</g>")
    shown = sorted(series)[:max_states]
    for k, j in enumerate(shown):
        pts = sorted(series[j], key=lambda p: xs.index(p["value"]))
        hue = int(210 + k * 24) % 360
        col = f"hsl({hue} 55% 42%)"
        path = " ".join(f"{'M' if i == 0 else 'L'}{X(p['value']):.1f},"
                        f"{Y(float(p['ours'])):.1f}" for i, p in enumerate(pts))
        out.append(f'<path d="{path}" fill="none" stroke="{col}" '
                   f'stroke-width="1.6"/>')
        for p in pts:
            disagrees = p.get("iso") and str(p["iso"]) not in (
                p["ours"], p["ours"] + ".0")
            out.append(
                f'<circle cx="{X(p["value"]):.1f}" cy="{Y(float(p["ours"])):.1f}" '
                f'r="{3.4 if disagrees else 2.4}" fill="{RED if disagrees else col}">'
                f'<title>{escape(j)} at {escape(str(p["value"]))}: '
                f'{escape(p["ours"])}'
                + (f' — ISO {escape(str(p["iso"]))}' if p.get("iso") else "")
                + "</title></circle>")
        last = pts[-1]
        out.append(_t(X(last["value"]) + 6, Y(float(last["ours"])) + 3, j,
                      9.5, col))
    if len(series) > max_states:
        out.append(_t(pad_l, h - 6, f"{len(series) - max_states} more "
                      f"jurisdictions not drawn", 9.5, MUTED))
    return _svg(w, h, "".join(out), f"Premium against {control_label}")


# --------------------------------------------------------------------- bars

def status_bars(summary: dict) -> str:
    """One run, as one bar. Not-applicable is grey and never counted as failure."""
    agree = summary.get("agree", 0)
    rated = summary.get("rated", 0)
    differ = len(summary.get("differ") or [])
    prem_only = len(summary.get("premium_only") or [])
    stopped = len(summary.get("engine_stopped") or [])
    na = len(summary.get("not_applicable") or [])
    errs = len(summary.get("errors") or [])
    if not summary.get("compared"):
        parts = [(rated, BLUE, "rated"), (stopped, RED, "engine refused"),
                 (errs, RED, "errors"), (na, GREY, "not applicable here")]
    else:
        parts = [(agree, BLUE, "agree with ISO"),
                 (prem_only, AMBER, "premium agrees, fields differ"),
                 (differ, RED, "disagree"), (stopped, RED, "engine refused"),
                 (errs, RED, "errors"), (na, GREY, "not applicable here")]
    parts = [p for p in parts if p[0]]
    total = sum(p[0] for p in parts) or 1
    w, h, bh = 620, 66, 22
    x, out = 0.0, []
    for n, col, label in parts:
        seg = n / total * w
        out.append(f'<rect x="{x:.1f}" y="4" width="{max(seg - 1, 1):.1f}" '
                   f'height="{bh}" fill="{col}" rx="2">'
                   f'<title>{n} {escape(label)}</title></rect>')
        if seg > 34:
            out.append(_t(x + seg / 2, 4 + bh / 2 + 4, str(n), 11, "#fff",
                          "middle", "600"))
        x += seg
    lx = 0.0
    for n, col, label in parts:
        out.append(f'<rect x="{lx:.1f}" y="{h - 18}" width="9" height="9" '
                   f'fill="{col}" rx="2"/>')
        out.append(_t(lx + 13, h - 10, f"{label} ({n})", 10, MUTED))
        lx += 26 + 6.0 * len(label)
    return _svg(w, h, "".join(out), "Outcomes for this run")
