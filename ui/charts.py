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

def _axis_order(xs: list) -> list:
    """Order the horizontal axis by magnitude when the values are amounts.

    **`"500,000 CSL"` sorts after `"2,000,000 CSL"` as text**, which draws a
    curve that climbs and then falls off a cliff -- a kink caused entirely by
    the axis. This chart exists to make a kink mean *a lookup missed*, so an
    ordering that invents one is worse than no chart. Values that do not all
    parse as numbers keep their text order, which is right for a categorical
    axis and is the only other kind this draws.
    """
    def amount(v):
        digits = ""
        for ch in str(v):
            if ch.isdigit() or (ch == "," and digits):
                digits += ch
            elif digits:
                break
        return float(digits.replace(",", "")) if digits else None

    keyed = [(amount(v), v) for v in xs]
    if all(k is not None for k, _ in keyed):
        return [v for _, v in sorted(keyed, key=lambda kv: kv[0])]
    return sorted(xs, key=str)


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
    xs = _axis_order(xs)
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

# --------------------------------------------------------------------- map

#: A tile grid, not a projection. Every jurisdiction gets the **same size
#: square**, which is the point: Rhode Island and Texas carry one submission
#: each, and a geographic map would draw Texas 200 times larger and say
#: something untrue about where the testing effort went. Rough US geography is
#: preserved so it is still findable at a glance.
#:
#: **Hawaii is drawn and permanently blank.** It is not in ISO's corpus at all,
#: and leaving it off the map would hide that; a grey tile labelled "not filed"
#: is the honest version.
TILES = {
    "AK": (0, 0),  "ME": (0, 10),
    "VT": (1, 8),  "NH": (1, 9),
    "WA": (2, 0),  "ID": (2, 1),  "MT": (2, 2),  "ND": (2, 3),  "MN": (2, 4),
    "IL": (2, 5),  "WI": (2, 6),  "MI": (2, 7),  "NY": (2, 8),  "RI": (2, 9),
    "MA": (2, 10),
    "OR": (3, 0),  "NV": (3, 1),  "WY": (3, 2),  "SD": (3, 3),  "IA": (3, 4),
    "IN": (3, 5),  "OH": (3, 6),  "PA": (3, 7),  "NJ": (3, 8),  "CT": (3, 9),
    "CA": (4, 0),  "UT": (4, 1),  "CO": (4, 2),  "NE": (4, 3),  "MO": (4, 4),
    "KY": (4, 5),  "WV": (4, 6),  "VA": (4, 7),  "MD": (4, 8),  "DC": (4, 9),
    "AZ": (5, 1),  "NM": (5, 2),  "KS": (5, 3),  "AR": (5, 4),  "TN": (5, 5),
    "NC": (5, 6),  "SC": (5, 7),  "DE": (5, 8),
    "OK": (6, 3),  "LA": (6, 4),  "MS": (6, 5),  "AL": (6, 6),  "GA": (6, 7),
    "HI": (7, 0),  "TX": (7, 3),  "FL": (7, 8),  "PR": (7, 9),
}

#: What a tile can say. Ordered worst-first: a jurisdiction with any
#: disagreement is drawn as disagreeing, however much else agreed.
MAP_STATES = (
    ("differs", RED, "disagrees with ISO"),
    ("refused", AMBER, "our engine refused"),
    ("agrees", BLUE, "every scenario agrees"),
    ("partial", "#8fb4d8", "agrees; some not offered here"),
    ("uncompared", GREY, "rated, never compared"),
    ("untested", "#e6e8ec", "never tested"),
    ("absent", "#f2f3f5", "not filed by ISO"),
)


def usa_map(status: dict, title: str = "") -> str:
    """One square per jurisdiction, coloured by the worst outcome seen there.

    `status` maps a jurisdiction to one of `MAP_STATES`. Anything absent is
    drawn `untested`, which is a real answer and the most common one early on.
    """
    cell, gap = 34, 4
    cols, rows = 11, 8
    w = cols * (cell + gap)
    h = rows * (cell + gap) + 46
    colour = {k: c for k, c, _ in MAP_STATES}
    body = []
    for juris, (r, c) in sorted(TILES.items()):
        st = "absent" if juris == "HI" else status.get(juris, "untested")
        fill = colour.get(st, colour["untested"])
        x, y = c * (cell + gap), r * (cell + gap)
        dark = st in ("differs", "refused", "agrees")
        body.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" '
            f'fill="{fill}"><title>{escape(juris)} - '
            f'{escape(dict((k, d) for k, _, d in MAP_STATES).get(st, st))}'
            f'</title></rect>'
            + _t(x + cell / 2, y + cell / 2 + 4, juris, 11,
                 "#fff" if dark else MUTED, "middle", "600"))

    # Legend, only for the states actually present, so it never explains a
    # colour that is not on the map.
    seen = {status.get(j, "untested") for j in TILES if j != "HI"} | {"absent"}
    lx, ly = 0, rows * (cell + gap) + 16
    for key, col, label in MAP_STATES:
        if key not in seen:
            continue
        body.append(f'<rect x="{lx}" y="{ly - 8}" width="9" height="9" rx="2" '
                    f'fill="{col}"/>')
        body.append(_t(lx + 13, ly, label, 10.5, MUTED))
        lx += 13 + 6.0 * len(label) + 14
        if lx > w - 90:
            lx, ly = 0, ly + 15
    return _svg(w, max(h, ly + 12), "".join(body), title)


def verdict(agree: int, differs: int, not_applicable: int, refused: int,
            uncompared: int = 0) -> str:
    """The one-screen answer: how much agrees, and what the worst problem is.

    **`not applicable` is drawn in its own colour and never inside the failure
    segment.** Conflating "ISO does not offer this here" with "we got it wrong"
    is this tool's easiest lie, and the percentage is computed over *comparable*
    outcomes only for the same reason.
    """
    comparable = agree + differs
    pct = (100.0 * agree / comparable) if comparable else 0.0
    total = max(1, agree + differs + not_applicable + refused + uncompared)
    w, h = 520, 132
    body = [_t(0, 40, f"{pct:.1f}%", 40, BLUE if not differs else RED,
               "start", "700")]
    body.append(_t(0, 60, f"{agree:,} of {comparable:,} comparable outcomes "
                          f"agree with ISO", 12, MUTED))

    x, y, bar = 0.0, 76.0, 14.0
    for n, col, label in ((agree, BLUE, "agrees"),
                          (uncompared, "#9fb8d4", "rated, not compared"),
                          (not_applicable, GREY, "not offered there"),
                          (refused, AMBER, "engine refused"),
                          (differs, RED, "disagrees")):
        if not n:
            continue
        seg = w * n / total
        body.append(f'<rect x="{x:.1f}" y="{y}" width="{max(seg, 1.5):.1f}" '
                    f'height="{bar}" fill="{col}"><title>{label}: {n}</title>'
                    f'</rect>')
        x += seg

    lx, ly = 0.0, y + bar + 18
    for n, col, label in ((agree, BLUE, "agrees"),
                          (uncompared, "#9fb8d4", "rated, not compared"),
                          (not_applicable, GREY, "not offered there"),
                          (refused, AMBER, "engine refused"),
                          (differs, RED, "disagrees")):
        if not n:
            continue
        body.append(f'<rect x="{lx}" y="{ly - 8}" width="9" height="9" rx="2" '
                    f'fill="{col}"/>')
        txt = f"{label} {n:,}"
        body.append(_t(lx + 13, ly, txt, 10.5, MUTED))
        lx += 13 + 6.0 * len(txt) + 14
        if lx > w - 110:
            lx, ly = 0.0, ly + 15
    return _svg(w, max(h, ly + 10), "".join(body))


# ------------------------------------------------- the layered programme (2)

def premium_spread(points: list, title: str = "") -> str:
    """One premium per jurisdiction, sorted, with the tail called out.

    **The lead visual for a layer that holds one configuration.** L1 and L2 vary
    nothing across the run except the state, so the variation *is* the geography
    and a curve has no second axis to draw. A class being dearer in some states
    than others is what a loss cost is; what is worth looking at is the shape of
    the tail, where a state far outside the rest is either a real filed
    difference or our bug.

    `points` is `[{"juris", "ours", "iso"?, "status"?}]`. Order is imposed here,
    not by the caller, because the sort *is* the chart.
    """
    pts = [p for p in points if p.get("ours") not in (None, "")]
    if len(pts) < 2:
        return empty("a spread needs two or more rated jurisdictions")
    pts = sorted(pts, key=lambda p: float(p["ours"]))
    w, h = 620, 190
    pad_l, pad_r, pad_b, pad_t = 46, 12, 34, 16
    vals = [float(p["ours"]) for p in pts]
    lo, hi = min(vals), max(vals)
    if hi == lo:
        hi = lo + 1
    # The median, because "far outside the rest" needs a rest to be outside of.
    mid = vals[len(vals) // 2]
    step = (w - pad_l - pad_r) / len(pts)
    bw = max(2.0, step - 3)
    out = [f'<line x1="{pad_l}" y1="{h - pad_b}" x2="{w - pad_r}" '
           f'y2="{h - pad_b}" stroke="{GRID}"/>',
           _t(pad_l - 6, pad_t + 6, f"{hi:,.0f}", 9.5, MUTED, "end"),
           _t(pad_l - 6, h - pad_b, f"{lo:,.0f}", 9.5, MUTED, "end")]
    for i, p in enumerate(pts):
        v = float(p["ours"])
        bh = max(1.0, (v - lo) * (h - pad_b - pad_t) / (hi - lo))
        x = pad_l + i * step
        y = h - pad_b - bh
        # Twice the median is the callout, and it is a rule of thumb stated on
        # the chart rather than a threshold hidden in the code.
        tail = v >= mid * 2
        differs = p.get("status") in ("DIFF", "PREMIUM ONLY")
        col = RED if (tail or differs) else BLUE
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
            f'fill="{col}" opacity="{0.95 if (tail or differs) else 0.55}">'
            f'<title>{escape(p["juris"])}: {escape(str(p["ours"]))}'
            + (f' — ISO {escape(str(p["iso"]))}' if p.get("iso") else "")
            + "</title></rect>")
        if tail:
            out.append(_t(x + bw / 2, y - 4, p["juris"], 9, RED, "middle", "650"))
    out.append(_t(pad_l, h - 6,
                  f"{len(pts)} jurisdictions, cheapest first · "
                  f"named above twice the median ({mid:,.0f})", 9.5, MUTED))
    return _svg(w, h, "".join(out), title or "Premium by jurisdiction")


def slot_bars(items: list, title: str = "") -> str:
    """How far each named thing moved the premium. One bar, no ordering implied.

    **The lead visual for L4.** Its six deductible slots are not a scale -- a
    line through them would invent an ordering ISO does not file -- so the
    question *is any slot ignored* is asked as six independent bars.

    `items` is `[{"label", "pct", "states", "moved_in"}]`, where `pct` is the
    mean change from the unvaried base. A bar that is zero everywhere is drawn
    red: a slot that moved nothing in any state either is a fact about ISO's
    filing or is a deductible we never applied, and those are very different.
    """
    items = list(items or [])
    if not items:
        return empty("no slots were exercised in this run")
    w = 620
    row_h, pad_t, pad_l = 26, 14, 200
    h = pad_t + row_h * len(items) + 22
    widest = max(abs(float(i.get("pct") or 0)) for i in items) or 1.0
    span = w - pad_l - 90
    out = []
    for k, it in enumerate(items):
        y = pad_t + k * row_h
        pct = float(it.get("pct") or 0)
        dead = not it.get("moved_in")
        bw = max(2.0, abs(pct) / widest * span) if pct else 2.0
        col = RED if dead else BLUE
        out.append(_t(pad_l - 10, y + 12, it["label"], 11, INK, "end"))
        out.append(f'<rect x="{pad_l}" y="{y + 3}" width="{bw:.1f}" height="13" '
                   f'rx="2" fill="{col}" opacity="{0.95 if dead else 0.6}">'
                   f'<title>{escape(it["label"])}: {pct:+.2f}% mean change, '
                   f'moved in {it.get("moved_in", 0)} of '
                   f'{it.get("states", 0)} jurisdictions</title></rect>')
        label = (f"{pct:+.2f}%" if pct else "0.00%")
        if dead:
            label += "  — moved nothing anywhere"
        out.append(_t(pad_l + bw + 7, y + 14, label, 10.5,
                      RED if dead else MUTED, "start", "650" if dead else "400"))
    out.append(_t(pad_l, h - 6, "mean change from the unvaried base", 9.5, MUTED))
    return _svg(w, h, "".join(out), title or "Movement by slot")
