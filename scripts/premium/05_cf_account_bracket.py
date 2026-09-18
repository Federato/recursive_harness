#!/usr/bin/env python3
"""Commercial Property account premium bracket, at cause-of-loss form granularity.

    python scripts/premium/05_cf_account_bracket.py

Every rating item (Building, Business Income, Contents) carries FOUR coverage
records -- Basic Group I, Basic Group II, Broad, Special -- each a separate leaf
with its own Premium. Their gates are NOT mutually exclusive:

    BasicGroupI / BasicGroupII : on whenever CauseOfLossToUse is set at all
    Broad                      : on only when CauseOfLossToUse = "Broad"
    Special                    : on only when CauseOfLossToUse = "Special"

so a Special-form item produces THREE premiums (BGI + BGII + Special), not one.
Columns are depth: Building enters at 3, Business Income at 4, Contents at 5.
Field names and structure are real (CFCW20260601V01); amounts are placeholders.
"""
import io, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "CF_Algorithm", "CF_Account_Premium_Bracket.html")


def split(bgi, bgii, broad, special):
    return {"BasicGroupI": bgi, "BasicGroupII": bgii, "Broad": broad, "Special": special}


ACCOUNT = [
 {"loc": "Location 1", "note": "Main St", "structures": [
   {"id": "Structure 1", "note": "masonry · CauseOfLoss Special", "terr": 45,
    "bldg": split(3400, 2100, 0, 700),
    "bi": {"terr": 22, "amt": split(1700, 1050, 0, 350)},
    "occ": [{"id": "OccupClass 1A", "note": "restaurant", "terr": 18,
             "pp": split(1350, 830, 0, 270)},
            {"id": "OccupClass 1B", "note": "retail", "terr": 9,
             "pp": split(650, 400, 0, 130)}]},
   {"id": "Structure 2", "note": "frame · CauseOfLoss Special", "terr": 28,
    "bldg": split(2150, 1320, 0, 430), "bi": None,
    "occ": [{"id": "OccupClass 2A", "note": "office", "terr": 0,
             "pp": split(900, 560, 0, 180)}]},
 ]},
 {"loc": "Location 2", "note": "Warehouse Rd", "structures": [
   {"id": "Structure 3", "note": "non-combustible · Special", "terr": 37,
    "bldg": split(2780, 1710, 0, 560),
    "bi": {"terr": 16, "amt": split(1270, 780, 0, 250)},
    "occ": [{"id": "OccupClass 3A", "note": "storage", "terr": 27,
             "pp": split(2050, 1260, 0, 410)}]},
 ]},
]

FORMS = ["BasicGroupI", "BasicGroupII", "Broad", "Special"]
ROW, BOXH, BOXH2, COLW, GAP = 26, 20, 32, 214, 28
PADT, PADL = 120, 20
MAXD = 5

nodes, edges = [], []
y = PADT


def add(depth, label, amt, kind, ytop, tag=None, note=None):
    n = {"x": PADL + (MAXD - depth) * (COLW + GAP), "y": ytop, "d": depth,
         "label": label, "amt": amt, "kind": kind, "tag": tag, "note": note,
         "h": BOXH2 if tag else BOXH}
    nodes.append(n)
    return n


def forms_block(depth, prefix, amounts, live_kind):
    """One leaf per cause-of-loss form. Returns (leaf nodes, their total)."""
    global y
    out = []
    for f in FORMS:
        amt = amounts[f]
        out.append(add(depth, "%s %s" % (prefix, f), amt, live_kind if amt else "off", y))
        y += ROW
    return out, sum(amounts.values())


def centre(ns, h):
    lo = min(k["y"] + k["h"] / 2 for k in ns)
    hi = max(k["y"] + k["h"] / 2 for k in ns)
    return (lo + hi) / 2 - h / 2


loc_nodes, terr = [], {"Structure": [], "PrsnlProp": [], "BusnInc": []}

for loc in ACCOUNT:
    st_nodes = []
    for st in loc["structures"]:
        kids = []
        bl, _ = forms_block(3, "Bldg", st["bldg"], "bldg")
        kids += bl
        terr["Structure"].append(st["terr"])
        if st["bi"]:
            bil, bitot = forms_block(4, "BI", st["bi"]["amt"], "bi")
            bagg = add(3, "CommercialPropertyBusinessIncome", bitot, "agg",
                       centre(bil, BOXH2), "Business Income")
            for k in bil:
                edges.append((k, bagg))
            kids.append(bagg)
            terr["BusnInc"].append(st["bi"]["terr"])
        for oc in st["occ"]:
            ppl, pptot = forms_block(5, "Contents", oc["pp"], "pp")
            ppagg = add(4, "CommercialPropertyPersonalProperty", pptot, "agg",
                        centre(ppl, BOXH))
            for k in ppl:
                edges.append((k, ppagg))
            ocagg = add(3, "CommercialPropertyOccupClass", pptot, "agg",
                        centre(ppl, BOXH2), oc["id"], oc["note"])
            edges.append((ppagg, ocagg))
            kids.append(ocagg)
            terr["PrsnlProp"].append(oc["terr"])
        ssum = sum(k["amt"] for k in kids)
        snode = add(2, "CommercialPropertyStructure", ssum, "agg",
                    centre(kids, BOXH2), st["id"], st["note"])
        for k in kids:
            edges.append((k, snode))
        st_nodes.append(snode)
        y += 14
    lnode = add(1, "CommercialPropertyLocation", sum(s["amt"] for s in st_nodes), "agg",
                centre(st_nodes, BOXH2), loc["loc"], loc["note"])
    for s in st_nodes:
        edges.append((s, lnode))
    loc_nodes.append(lnode)
    y += 22

y += 14
tot_st, tot_pp, tot_bi = (sum(terr["Structure"]), sum(terr["PrsnlProp"]), sum(terr["BusnInc"]))
tria_amt = tot_st + tot_pp + tot_bi
tria = add(1, "CommercialPropertyPostTRIACoverage", tria_amt, "tria", y,
           "TRIA accepted", "policy-level leaf")
y += BOXH2 + 10

total = sum(n["amt"] for n in loc_nodes) + tria_amt
allk = loc_nodes + [tria]
pol = add(0, "CommercialProperty", total, "total", centre(allk, BOXH2), "POLICY TOTAL")
for k in allk:
    edges.append((k, pol))

W = PADL + (MAXD + 1) * (COLW + GAP) + 26
H = y + 60

COLORS = {"bldg": ("#1f3864", "#e8edf5"), "pp": ("#6b4c9a", "#efeaf7"),
          "bi": ("#a35a1e", "#f7ece0"), "tria": ("#7a1f3d", "#f5e3ea"),
          "agg": ("#2f7d5a", "#e4f1ea"), "total": ("#0f2740", "#cfd9e6"),
          "off": ("#9aa4ae", "#f2f3f5")}
SHORT = {"CommercialPropertyPersonalProperty": "CP·PersonalProperty",
         "CommercialPropertyOccupClass": "CP·OccupClass",
         "CommercialPropertyBusinessIncome": "CP·BusinessIncome",
         "CommercialPropertyStructure": "CP·Structure",
         "CommercialPropertyLocation": "CP·Location",
         "CommercialPropertyPostTRIACoverage": "CP·PostTRIACoverage",
         "CommercialProperty": "CommercialProperty"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


svg = ['<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" '
       'preserveAspectRatio="xMinYMin meet" '
       'font-family="ui-monospace,Consolas,monospace">' % (W, H)]
heads = [("depth 5", "Contents coverage"), ("depth 4", "PersonalProperty / BI coverage"),
         ("depth 3", "OccupClass / BI / Building cov"), ("depth 2", "Structure"),
         ("depth 1", "Location / policy leaf"), ("depth 0", "Policy total")]
for i, (a, b) in enumerate(heads):
    x = PADL + i * (COLW + GAP)
    svg.append('<text x="%d" y="%d" font-size="10" font-weight="700" fill="#8b95a1" '
               'font-family="-apple-system,Segoe UI,sans-serif" letter-spacing=".07em">%s</text>'
               % (x, PADT - 46, esc(a.upper())))
    svg.append('<text x="%d" y="%d" font-size="10.5" font-weight="700" fill="#55606b" '
               'font-family="-apple-system,Segoe UI,sans-serif">%s</text>'
               % (x, PADT - 30, esc(b)))

for a, b in edges:
    x1, y1 = a["x"] + COLW, a["y"] + a["h"] / 2
    x2, y2 = b["x"], b["y"] + b["h"] / 2
    mx = x1 + (x2 - x1) / 2
    dash = ' stroke-dasharray="2,3"' if a["kind"] == "off" else ""
    svg.append('<path d="M%.1f %.1f H%.1f V%.1f H%.1f" fill="none" stroke="#c3cad3" '
               'stroke-width="1.1"%s/>' % (x1, y1, mx, y2, x2, dash))

for n in nodes:
    stroke, fill = COLORS[n["kind"]]
    svg.append('<rect x="%d" y="%.1f" width="%d" height="%d" rx="4" fill="%s" stroke="%s" '
               'stroke-width="1.1"%s/>'
               % (n["x"], n["y"], COLW, n["h"], fill, stroke,
                  ' stroke-dasharray="3,2"' if n["kind"] == "off" else ""))
    lab = SHORT.get(n["label"], n["label"])
    if len(lab) > 28:
        lab = lab[:27] + "…"
    svg.append('<text x="%d" y="%.1f" font-size="9" fill="%s">%s</text>'
               % (n["x"] + 7, n["y"] + 13.5, stroke, esc(lab)))
    svg.append('<text x="%d" y="%.1f" font-size="9" font-weight="700" fill="%s" '
               'text-anchor="end">%s</text>'
               % (n["x"] + COLW - 7, n["y"] + 13.5, stroke, "{:,}".format(n["amt"])))
    if n.get("tag"):
        tg = esc(n["tag"]) + (" · " + esc(n["note"]) if n.get("note") else "")
        svg.append('<text x="%d" y="%.1f" font-size="8" fill="%s" opacity="0.78" '
                   'font-family="-apple-system,Segoe UI,sans-serif">%s</text>'
                   % (n["x"] + 7, n["y"] + 25, stroke, tg[:40]))
svg.append("</svg>")

n_leaf = sum(1 for n in nodes if n["kind"] in ("bldg", "bi", "pp", "off"))
n_off = sum(1 for n in nodes if n["kind"] == "off")

html = """<title>CF account premium bracket &mdash; cause-of-loss form granularity</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
 body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 margin:0;padding:30px 26px 80px;color:#1c2733;background:#fbfbfd;line-height:1.55}
 @media(prefers-color-scheme:dark){body{background:#14181d;color:#dfe4e9}
  svg text[fill="#55606b"],svg text[fill="#8b95a1"]{fill:#93a0ad}
  svg rect{filter:brightness(.34) saturate(1.5)} svg path{stroke:#3a434e}}
 h1{font-size:21px;font-weight:600;margin:0 0 4px}
 h2{font-size:16px;margin:28px 0 8px}
 .sub{font-size:13.5px;color:#55606b;margin:0 0 4px;max-width:940px}
 @media(prefers-color-scheme:dark){.sub{color:#93a0ad}}
 .wrap{margin:22px 0 10px}
 svg{width:100%%;height:auto;display:block}
 code{font-family:ui-monospace,Consolas,monospace;font-size:12.5px;background:#eef1f4;
 padding:1px 5px;border-radius:3px}
 @media(prefers-color-scheme:dark){code{background:#222a33}}
 .key{display:flex;flex-wrap:wrap;gap:15px;margin:14px 0 0;font-size:12.5px}
 .key i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;
 vertical-align:-1px;border:1.2px solid}
 table{border-collapse:collapse;margin:16px 0;font-size:13px}
 th,td{border:1px solid #d7dce2;padding:6px 10px;text-align:left;vertical-align:top}
 @media(prefers-color-scheme:dark){th,td{border-color:#2f3740}}
 th{background:#1f3864;color:#fff;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
 .warn{background:#f7ddd4;color:#a53d26;padding:10px 14px;border-radius:6px;font-size:13px;
 margin:16px 0;max-width:940px}
 @media(prefers-color-scheme:dark){.warn{background:#2c221c;color:#e09a80}}
 .good{background:#dcefe4;color:#2f7d5a}
 @media(prefers-color-scheme:dark){.good{background:#16291f;color:#63c090}}
</style>

<h1>Commercial Property &mdash; account premium bracket</h1>
<p class="sub">Two locations, three buildings, four occupancy classes, business income on two,
TRIA accepted, every item written on the <b>Special</b> cause-of-loss form. Drawn at
<b>cause-of-loss form granularity</b>: <b>%d</b> leaf coverage records, of which <b>%d</b> are
gated off. Every box is a real datadef field from <code>CFCW20260601V01</code>.</p>

<div class="warn"><b>The amounts are placeholders.</b> Structure, field names and the
arithmetic of the roll-up are real; no premium was computed.</div>

<div class="key">
 <span><i style="background:#e8edf5;border-color:#1f3864"></i>Building</span>
 <span><i style="background:#f7ece0;border-color:#a35a1e"></i>Business Income</span>
 <span><i style="background:#efeaf7;border-color:#6b4c9a"></i>Contents</span>
 <span><i style="background:#f5e3ea;border-color:#7a1f3d"></i>TRIA</span>
 <span><i style="background:#e4f1ea;border-color:#2f7d5a"></i><code>ErcCalculatedTotalPremium</code></span>
 <span><i style="background:#f2f3f5;border-color:#9aa4ae;border-style:dashed"></i>gated off &mdash; contributes 0</span>
</div>

<div class="wrap">%s</div>

<h2>Four coverage records per item &mdash; and they are not mutually exclusive</h2>
<p class="sub">Building, Business Income and Contents each file <b>four</b> separate coverage
records &mdash; Basic Group I, Basic Group II, Broad, Special &mdash; each a leaf with its own
<code>Premium</code>, its own <code>SetPremium</code> and its own gate. The gates are the part
that surprises:</p>
<table>
<thead><tr><th>Record</th><th><code>SetCoverageOnPolicyIndicator</code> condition</th>
<th>On when cause of loss is&hellip;</th></tr></thead>
<tbody>
<tr><td>Basic Group I</td><td><code>CauseOfLossToUse &ne; "Not Applicable" AND &ne; ""</code></td>
 <td><b>Basic, Broad <i>and</i> Special</b> &mdash; any selection at all</td></tr>
<tr><td>Basic Group II</td><td><code>CauseOfLossToUse &ne; "Not Applicable" AND &ne; ""</code></td>
 <td><b>Basic, Broad <i>and</i> Special</b> &mdash; any selection at all</td></tr>
<tr><td>Broad</td><td><code>CauseOfLossToUse = "Broad"</code></td><td>Broad only</td></tr>
<tr><td>Special</td><td><code>CauseOfLossToUse = "Special"</code></td><td>Special only</td></tr>
</tbody>
</table>
<div class="warn good"><b>A Special-form building therefore produces three premiums, not one:</b>
Basic Group I <b>+</b> Basic Group II <b>+</b> Special. Broad is the only record switched off.
A Basic-form item produces two (BGI + BGII); a Broad-form item produces three
(BGI + BGII + Broad).</div>
<p class="sub">The filed rates confirm the forms are <b>incremental, not alternative</b>. Alabama,
class 0701 masonry: Basic Group I base rate <b>0.115</b>, Basic Group II
<b>0.080&ndash;0.156</b> by construction symbol, and the Special building rate a flat
<b>0.039</b> &mdash; far too small to replace the other two, and exactly the shape of a top-up
for the extra perils Special adds.</p>

<h2>The depths</h2>
<table>
<thead><tr><th>Coverage</th><th>Leaf group (one per form)</th><th>Depth</th><th>Path to the policy total</th></tr></thead>
<tbody>
<tr><td><b>Building</b></td><td><code>CommercialPropertyStructureBuilding&lt;Form&gt;Coverage</code></td>
 <td>3</td><td>Structure &rarr; Location &rarr; CommercialProperty</td></tr>
<tr><td><b>Business Income</b></td><td><code>CommercialPropertyBusinessIncome&lt;Form&gt;Coverage</code></td>
 <td>4</td><td>BusinessIncome &rarr; Structure &rarr; Location &rarr; CommercialProperty</td></tr>
<tr><td><b>Contents</b></td><td><code>CommercialPropertyPersonalPropertyPrsnlProp&lt;Form&gt;Coverage</code></td>
 <td>5</td><td>PersonalProperty &rarr; OccupClass &rarr; Structure &rarr; Location &rarr; CommercialProperty</td></tr>
</tbody>
</table>
<p class="sub">Business Income hangs off the <i>building</i>, not the occupancy class &mdash; so a
building with two occupancy classes has one business-income record and two contents records,
each still carrying its own four forms.</p>

<h2>TRIA does not roll up like the others</h2>
<p class="sub"><code>CommercialPropertyPostTRIACoverage</code> is a single policy-level leaf at
depth 1. Its <code>SetPremium</code> is
<code>round(TotalStructurePremium + TotalPrsnlPropPremium + TotalBusnIncPremium +
TotalSpecialPremium + TotalSpClBusnIncPremium)</code>, and each of those five is built on the
same record by <code>Sum(ForEach Location &rarr; ForEach item &rarr; that item's
TerrorismPremium)</code>.</p>
<div class="warn"><b>Those five are the only per-coverage account totals CF stores &mdash; and
they total <i>terrorism</i> premium, not coverage premium.</b> There is still no field holding
the account's total building premium or total contents premium.</div>
<table>
<thead><tr><th>Per-item terrorism</th><th>Accumulator</th><th>Value here</th></tr></thead>
<tbody>
<tr><td>3 Structure records</td><td><code>TotalStructurePremium</code></td><td>%d</td></tr>
<tr><td>4 PersonalProperty records</td><td><code>TotalPrsnlPropPremium</code></td><td>%d</td></tr>
<tr><td>2 BusinessIncome records</td><td><code>TotalBusnIncPremium</code></td><td>%d</td></tr>
<tr><td colspan="2"><b><code>PostTRIACoverage.Premium</code></b></td><td><b>%d</b></td></tr>
</tbody>
</table>

<h2>The gate every leaf passes</h2>
<p class="sub">A leaf contributes its <code>Premium</code> only when
<code>PremiumIndicator = 1</code> <b>and</b> <code>Premium &ne; 0</code>. The dashed boxes are
Broad records that exist and rate but contribute nothing &mdash; indistinguishable in the total
from a coverage that was never bought.</p>
""" % (n_leaf, n_off, "\n".join(svg), tot_st, tot_pp, tot_bi, tria_amt)

io.open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
print("nodes", len(nodes), "edges", len(edges), "| leaves", n_leaf, "gated off", n_off)
print("terrorism %d + %d + %d = %d" % (tot_st, tot_pp, tot_bi, tria_amt))
print("POLICY TOTAL", "{:,}".format(total))
