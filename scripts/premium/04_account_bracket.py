"""Render an account-level premium bracket: leaf Premium fields -> policy total.

    python scripts/premium/04_account_bracket.py

Edit the `account` dict below to model a different risk. Structure and field
names are real; amounts are placeholders and are labelled as such on the page.

The structure and the field names are real (GL CW 20270401 V01). The dollar
amounts are placeholders chosen to make the summation legible -- they are not
rated values and are labelled as such on the page.
"""
import io, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = r"C:\Projects\Recursive_Harness_2.0\GL_Algorithm\GL_Account_Premium_Bracket.html"

# ---- the account -------------------------------------------------------------
# leaf = (field path suffix, label, amount, kind)
def cov(n, amt, kind="cov"):
    return {"f": n, "amt": amt, "kind": kind}

account = {
    "locations": [
        {"id": "Location 1", "note": "Downtown", "classes": [
            {"id": "Classification 1A", "note": "class 16905 \u00b7 restaurant, liquor",
             "covs": [cov("ClassificationPremOpsCoverage", 4820),
                      cov("ClassificationProdsCompldOpsCoverage", 1140),
                      cov("ClassificationLiquorCoverage", 2310)],
             "terr": [cov("TerrorismPremOpsCoverage", 24, "terr"),
                      cov("TerrorismProdsCompldOpsCoverage", 6, "terr"),
                      cov("TerrorismAllOtherSublineCoverage", 12, "terr")]},
            {"id": "Classification 1B", "note": "class 18206 \u00b7 retail, no liquor",
             "covs": [cov("ClassificationPremOpsCoverage", 1960),
                      cov("ClassificationProdsCompldOpsCoverage", 640)],
             "terr": [cov("TerrorismPremOpsCoverage", 10, "terr"),
                      cov("TerrorismProdsCompldOpsCoverage", 3, "terr")]},
        ]},
        {"id": "Location 2", "note": "Airport", "classes": [
            {"id": "Classification 2A", "note": "class 16905 \u00b7 restaurant, liquor",
             "covs": [cov("ClassificationPremOpsCoverage", 3450),
                      cov("ClassificationProdsCompldOpsCoverage", 820),
                      cov("ClassificationLiquorCoverage", 1875)],
             "terr": [cov("TerrorismPremOpsCoverage", 17, "terr"),
                      cov("TerrorismProdsCompldOpsCoverage", 4, "terr"),
                      cov("TerrorismAllOtherSublineCoverage", 9, "terr")]},
        ]},
    ],
    # policy-level leaves that bypass the location chain entirely
    "policy_leaves": [
        cov("MedPayCoverage", 0, "zero"),
        cov("PremOpsPremiumToReachMinCoverage", 0, "slot"),
        cov("ProdsCompldOpsPremiumToReachMinCoverage", 0, "slot"),
        cov("LiquorPremiumToReachMinCoverage", 815, "slot"),
    ],
}

# ---- layout ------------------------------------------------------------------
ROW = 40          # vertical pitch per leaf
BOXH = 22
BOXH2 = 34        # box carrying an inside tag
COLW = 250
GAP = 34
PADT, PADL = 112, 20

nodes, edges = [], []
y = PADT


def add(col, label, sub, amt, kind, ytop):
    n = {"x": PADL + col * (COLW + GAP), "y": ytop, "label": label,
         "sub": sub, "amt": amt, "kind": kind, "col": col, "h": BOXH}
    nodes.append(n)
    return n


def tagged(n, tag, note=None):
    n["tag"] = tag
    if note:
        n["note"] = note
    n["h"] = BOXH2
    return n


loc_nodes = []
for loc in account["locations"]:
    cls_nodes = []
    for cl in loc["classes"]:
        leaf_nodes = []
        for c in cl["covs"]:
            leaf_nodes.append(add(0, c["f"], "Premium", c["amt"], c["kind"], y)); y += ROW
        terr_parent = None
        if cl["terr"]:
            tn = []
            for c in cl["terr"]:
                tn.append(add(0, c["f"], "Premium", c["amt"], c["kind"], y)); y += ROW
            tsum = sum(c["amt"] for c in cl["terr"])
            ty = (tn[0]["y"] + tn[-1]["y"]) / 2
            terr_parent = add(1, "GeneralLiabilityTerrorism", "ErcCalculatedTotalPremium",
                              tsum, "agg", ty)
            for a in tn:
                edges.append((a, terr_parent))
        kids = leaf_nodes + ([terr_parent] if terr_parent else [])
        csum = sum(c["amt"] for c in cl["covs"]) + (terr_parent["amt"] if terr_parent else 0)
        cy = (min(k["y"] + k["h"] / 2 for k in kids) + max(k["y"] + k["h"] / 2 for k in kids)) / 2 - BOXH2 / 2
        cnode = add(2, "GeneralLiabilityClassification", "ErcCalculatedTotalPremium",
                    csum, "agg", cy)
        tagged(cnode, cl["id"], cl["note"])
        for k in kids:
            edges.append((k, cnode))
        cls_nodes.append(cnode)
        y += 14
    lsum = sum(c["amt"] for c in cls_nodes)
    ly = (cls_nodes[0]["y"] + cls_nodes[-1]["y"]) / 2
    lnode = add(3, "GeneralLiabilityLocation", "ErcCalculatedTotalPremium", lsum, "agg", ly)
    tagged(lnode, loc["id"], loc["note"])
    for c in cls_nodes:
        edges.append((c, lnode))
    loc_nodes.append(lnode)
    y += 22

y += 10
policy_leaf_nodes = []
for c in account["policy_leaves"]:
    policy_leaf_nodes.append(add(3, c["f"], "Premium", c["amt"], c["kind"], y)); y += ROW

total = sum(n["amt"] for n in loc_nodes) + sum(n["amt"] for n in policy_leaf_nodes)
allk = loc_nodes + policy_leaf_nodes
pnode = add(4, "GeneralLiability", "ErcCalculatedTotalPremium", total, "total",
            (min(k["y"] + k["h"] / 2 for k in allk)
             + max(k["y"] + k["h"] / 2 for k in allk)) / 2 - BOXH2 / 2)
tagged(pnode, "POLICY TOTAL")
for k in allk:
    edges.append((k, pnode))

W = PADL + 5 * (COLW + GAP) + 40
H = y + 70

COLORS = {
    "cov":  ("#1f3864", "#e8edf5"),
    "terr": ("#6b4c9a", "#efeaf7"),
    "slot": ("#a35a1e", "#f7ece0"),
    "zero": ("#8b95a1", "#eef0f2"),
    "agg":  ("#2f7d5a", "#e4f1ea"),
    "total": ("#0f2740", "#cfd9e6"),
}


SHORT = {
    "ClassificationPremOpsCoverage":                  "Prem/Ops",
    "ClassificationProdsCompldOpsCoverage":           "Products/Compl Ops",
    "ClassificationLiquorCoverage":                   "Liquor",
    "TerrorismPremOpsCoverage":                       "Terrorism · Prem/Ops",
    "TerrorismProdsCompldOpsCoverage":                "Terrorism · Products",
    "TerrorismAllOtherSublineCoverage":               "Terrorism · All Other",
    "MedPayCoverage":                                 "MedPay (never computed)",
    "PremOpsPremiumToReachMinCoverage":               "Min top-up · Prem/Ops",
    "ProdsCompldOpsPremiumToReachMinCoverage":        "Min top-up · Products",
    "LiquorPremiumToReachMinCoverage":                "Min top-up · Liquor",
    "GeneralLiabilityTerrorism":                      "GL·Terrorism",
    "GeneralLiabilityClassification":                 "GL·Classification",
    "GeneralLiabilityLocation":                       "GL·Location",
    "GeneralLiability":                               "GeneralLiability",
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


svg = ['<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" '
       'preserveAspectRatio="xMinYMin meet" '
       'font-family="ui-monospace,Consolas,monospace">' % (W, H)]

# column headers
heads = ["Leaf records \u2014 field: Premium", "Terrorism subtotal",
         "Classification subtotal", "Location subtotal / policy leaves", "Policy total"]
for i, h in enumerate(heads):
    svg.append('<text x="%d" y="%d" font-size="11" font-weight="700" fill="#55606b" '
               'font-family="-apple-system,Segoe UI,sans-serif" letter-spacing="0.06em">%s</text>'
               % (PADL + i * (COLW + GAP), PADT - 34, esc(h.upper())))

for a, b in edges:
    x1, y1 = a["x"] + COLW, a["y"] + a["h"] / 2
    x2, y2 = b["x"], b["y"] + b["h"] / 2
    mx = x1 + (x2 - x1) / 2
    svg.append('<path d="M%.1f %.1f H%.1f V%.1f H%.1f" fill="none" stroke="#c3cad3" '
               'stroke-width="1.2"/>' % (x1, y1, mx, y2, x2))

for n in nodes:
    stroke, fill = COLORS[n["kind"]]
    svg.append('<rect x="%d" y="%.1f" width="%d" height="%d" rx="4" fill="%s" stroke="%s" '
               'stroke-width="1.2"/>' % (n["x"], n["y"], COLW, n["h"], fill, stroke))
    lab = SHORT.get(n["label"], n["label"].replace("GeneralLiability", "GL·"))
    if len(lab) > 31:
        lab = lab[:30] + "…"
    svg.append('<text x="%d" y="%.1f" font-size="9.5" fill="%s">%s</text>'
               % (n["x"] + 7, n["y"] + 14, stroke, esc(lab)))
    amt = ("{:,}".format(n["amt"]))
    svg.append('<text x="%d" y="%.1f" font-size="9.5" font-weight="700" fill="%s" '
               'text-anchor="end">%s</text>' % (n["x"] + COLW - 7, n["y"] + 14, stroke, amt))
    if n.get("tag"):
        tg = esc(n["tag"]) + (" · " + esc(n["note"]) if n.get("note") else "")
        svg.append('<text x="%d" y="%.1f" font-size="8.5" fill="%s" opacity="0.78" '
                   'font-family="-apple-system,Segoe UI,sans-serif">%s</text>'
                   % (n["x"] + 7, n["y"] + 27, stroke, tg[:40]))
svg.append("</svg>")
SVG = "\n".join(svg)

html = """<title>Account premium bracket &mdash; leaf Premium fields to policy total</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
 body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 margin:0;padding:30px 26px 80px;color:#1c2733;background:#fbfbfd;line-height:1.55}
 @media(prefers-color-scheme:dark){body{background:#14181d;color:#dfe4e9}
  svg text[fill="#55606b"]{fill:#93a0ad}
  svg rect{filter:brightness(.34) saturate(1.5)} svg path{stroke:#3a434e}}
 h1{font-size:21px;font-weight:600;margin:0 0 4px}
 .sub{font-size:13.5px;color:#55606b;margin:0 0 4px;max-width:900px}
 @media(prefers-color-scheme:dark){.sub{color:#93a0ad}}
 .wrap{margin:22px 0 10px}
 svg{width:100%%;height:auto;display:block}
 code{font-family:ui-monospace,Consolas,monospace;font-size:12.5px;background:#eef1f4;
 padding:1px 5px;border-radius:3px}
 @media(prefers-color-scheme:dark){code{background:#222a33}}
 .key{display:flex;flex-wrap:wrap;gap:16px;margin:14px 0 0;font-size:12.5px}
 .key i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;
 vertical-align:-1px;border:1.2px solid}
 table{border-collapse:collapse;margin:16px 0;font-size:13px}
 th,td{border:1px solid #d7dce2;padding:6px 10px;text-align:left}
 @media(prefers-color-scheme:dark){th,td{border-color:#2f3740}}
 th{background:#1f3864;color:#fff;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
 td.n{text-align:right;font-family:ui-monospace,Consolas,monospace}
 .warn{background:#f7ddd4;color:#a53d26;padding:10px 14px;border-radius:6px;font-size:13px;
 margin:16px 0;max-width:900px}
 @media(prefers-color-scheme:dark){.warn{background:#2c221c;color:#e09a80}}
</style>

<h1>Account premium bracket</h1>
<p class="sub">Two locations, three classifications, liquor liability on two of them, terrorism
accepted. Every box is a real datadef field from <code>GL CW 20270401 V01</code>. Read left to
right: each leaf holds a <code>Premium</code>; each merge is one
<code>CalculateTotalPremium</code> writing an <code>ErcCalculatedTotalPremium</code>.</p>

<div class="warn"><b>The amounts are placeholders.</b> They exist to make the summation legible
and are not rated values &mdash; no premium was computed. The <i>structure</i>, the field names
and the arithmetic of the roll-up are real.</div>

<div class="key">
 <span><i style="background:#e8edf5;border-color:#1f3864"></i>coverage <code>Premium</code></span>
 <span><i style="background:#efeaf7;border-color:#6b4c9a"></i>terrorism <code>Premium</code></span>
 <span><i style="background:#e4f1ea;border-color:#2f7d5a"></i><code>ErcCalculatedTotalPremium</code></span>
 <span><i style="background:#f7ece0;border-color:#a35a1e"></i>caller-supplied slot</span>
 <span><i style="background:#eef0f2;border-color:#8b95a1"></i>never computed (always 0)</span>
</div>

<div class="wrap">%s</div>

<h2 style="font-size:16px;margin-top:26px">What each merge is</h2>
<table>
<thead><tr><th>Level</th><th>Field written</th><th>Rule</th><th>Inputs</th></tr></thead>
<tbody>
<tr><td>leaf</td><td><code>Premium</code></td><td><code>SetPremium</code></td>
 <td><code>FinalRate &times; Exposure &divide; 1000</code>, rounded to whole dollars</td></tr>
<tr><td>terrorism</td><td><code>GeneralLiabilityTerrorism.ErcCalculatedTotalPremium</code></td>
 <td><code>CalculateTotalPremium</code></td><td>its three coverage <code>Premium</code> fields</td></tr>
<tr><td>classification</td><td><code>GeneralLiabilityClassification.ErcCalculatedTotalPremium</code></td>
 <td><code>CalculateTotalPremium</code></td>
 <td>Prem/Ops + Products + Liquor + the terrorism subtotal</td></tr>
<tr><td>location</td><td><code>GeneralLiabilityLocation.ErcCalculatedTotalPremium</code></td>
 <td><code>CalculateTotalPremium</code></td><td>its classification subtotals</td></tr>
<tr><td>policy</td><td><code>GeneralLiability.ErcCalculatedTotalPremium</code></td>
 <td><code>CalculateTotalPremium</code></td>
 <td>location subtotals <b>+</b> the policy-level leaves</td></tr>
</tbody>
</table>

<h2 style="font-size:16px;margin-top:30px">Per-coverage totals &mdash; where they exist</h2>
<p class="sub">The bracket above aggregates by <b>record hierarchy</b>: classification, then
location, then policy. It never aggregates by <b>coverage</b>. With three classifications
across two locations there are three Prem/Ops <code>Premium</code> values and, on an ordinary
policy, <b>no field anywhere holding their sum</b>.</p>

<p class="sub">ISO does compute per-coverage account totals &mdash; in two places, both
conditional, and neither of them on the path the bracket draws.</p>

<table>
<thead><tr><th>Where</th><th>What</th><th>Form</th><th>When it runs</th></tr></thead>
<tbody>
<tr><td><code>GeneralLiabilityCompositeRating</code></td>
 <td><b>Twelve per-coverage totals</b>, one per coverage &mdash;
 <code>premOpsCoverageTotalPremium</code>, <code>prodsCompldOpsCoverageTotalPremium</code>,
 <code>liquorCoverageTotalPremium</code>, the three terrorism ones, Owners&amp;Contractors,
 Railroad, Snowplow, Canoes, and both Product Withdrawal exclusions. Each is
 <code>Sum(ForEach location &rarr; ForEach classification &rarr; that coverage's Premium)</code></td>
 <td><b>Rules, not fields.</b> They return a value; only their sum is stored, as
 <code>TotalClassificationsPremium</code></td>
 <td><b>Only when <code>CompositeRating = "Yes"</code></b></td></tr>
<tr><td>the <code>&hellip;PremiumToReachMinCoverage</code> records</td>
 <td><b>Four stored coverage totals</b> &mdash;
 <code>TotalCyberIncidentLiabilityPremium</code>,
 <code>TotalLossOfElectronicDataPremium</code>, <code>TotalUnmannedAircraftPremium</code>,
 <code>LimitedProductWithdrawalClassPremium</code></td>
 <td>Real datadef fields, written by a <code>Set&hellip;</code> rule</td>
 <td>When that coverage is on the policy &mdash; they exist to be compared against a minimum</td></tr>
<tr><td>Prem/Ops, Products, Liquor on an ordinary policy</td>
 <td><b>Nothing</b></td><td>&mdash;</td>
 <td>Never. No <code>TotalPremOpsPremium</code> or <code>TotalProdsCompldOpsPremium</code>
 field is declared anywhere in the DataDef</td></tr>
</tbody>
</table>

<div class="warn"><b>Read that carefully before concluding ISO does not total by coverage.</b>
A search over datadef <i>field names</i> says it does not. That is wrong &mdash; the totals are
<i>rules</i> that return values without ever writing a field, so a field-name search cannot see
them. What is true is narrower: <b>per-coverage totals are computed only under composite
rating, or where a coverage needs one to test a minimum premium.</b> On the ordinary policy the
bracket draws, no per-coverage total is produced or stored.</div>

<p class="sub">Two related figures do sit on <code>GeneralLiability</code> and are easy to
mistake for the answer: <code>AnnualBasicLimitsCoPremiumPremOps</code> and
<code>AnnualBasicLimitsCoPremiumProdCompldOps</code>. They are built from
<code>BasicLimitPremium</code>, not <code>Premium</code> &mdash; basic-limits sums for
statistical reporting, a different quantity from what the coverage cost.</p>

<h2 style="font-size:16px;margin-top:26px">Three things the bracket shows</h2>
<p class="sub"><b>1 &middot; Liquor is per classification, not per policy.</b> It appears only
where a classification has liquor exposure &mdash; 1A and 2A here, not 1B. There is no
policy-level liquor premium; the account's liquor cost is the sum of its classifications'.</p>
<p class="sub"><b>2 &middot; The policy-level leaves bypass the location chain.</b> Med Pay and
the three <code>PremiumToReachMin</code> records attach directly to
<code>GeneralLiability</code>, so they are added <i>after</i> every location has been totalled.
The liquor minimum top-up of 815 shown here is <b>supplied by the caller</b> &mdash; no rule
computes it.</p>
<p class="sub"><b>3 &middot; Every merge applies the same gate.</b> A leaf contributes its
<code>Premium</code> only when <code>PremiumIndicator = 1</code> <b>and</b>
<code>Premium &ne; 0</code>. <code>MedPayCoverage.Premium</code> sits at 0 because nothing ever
computes it &mdash; Med Pay is priced as a factor inside the Prem/Ops <code>FinalILF</code>.</p>
""" % SVG

io.open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
print("nodes", len(nodes), "edges", len(edges), "policy total", format(total, ","))
for n in nodes:
    if n.get("tag"):
        print("   %-22s %10s" % (n["tag"], format(n["amt"], ",")))
