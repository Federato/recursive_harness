"""Plain words for the Carrier Filings screen: one place that turns codes into what they mean.

The screen is read by underwriters, product people and executives alike, so the main view says what a filing does
in ordinary words ("Premises and operations: 6% below ISO") and keeps the technical names (`LCM:PremOps 0.942`) for
a "Show technical" view. Everything here is wording; nothing rates.
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

LINES = {"GL": "General Liability", "CF": "Commercial Property"}

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
    "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "PR": "Puerto Rico", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

#: What each rate a filing can change covers, said plainly.
TARGETS = {
    "PremOps": "Premises and operations",
    "ProdsCompldOps": "Products and completed work",
    "GroupI": "Fire and lightning",
    "GroupII": "Wind and hail",
    "Broad": "Broad form",
    "Special": "Special form",
    "Earthquake": "Earthquake",
    "All": "Every coverage",
}

#: The filing's stages, as the screen names them.
STAGES = {"Received": "Received", "Mapped": "Reviewed", "Draft impact": "Impact checked", "Built": "In use",
          "Proved": "Proven"}
STEPS = ["Received", "Reviewed", "Impact checked", "In use", "Proven"]

CELL = {"approved": "In use", "draft": "Proposed", "proposed": "Proposed", "withdrawn": "Withdrawn",
        "rejected": "Rejected"}

GLOSSARY = [
    ("ISO", "Insurance Services Office: publishes the standard rates, rules and forms most US commercial insurers start from."),
    ("Rate filing", "An insurer's request, approved by the state, to charge differently from ISO."),
    ("Loss cost multiplier", "The factor an insurer applies to ISO's loss costs. 1.10 means 10% above ISO; 0.94 means 6% below."),
    ("Class", "ISO's code for the kind of business, for example a retail store or a contractor."),
    ("\"a\"-rated class", "A specialty class ISO publishes no rate for; the insurer sets the rate itself."),
    ("Effective dates", "When the filing starts: one date for new policies, often a later one for renewals."),
    ("ISO edition", "ISO revises its rates; a filing's changes always apply to ISO's rates in force on the policy date."),
    ("Projected book", "A set of typical businesses we rate both ways to estimate the effect. No real customers."),
]


def money_date(iso: str | None) -> str:
    """'2025-07-15' -> 'Jul 15, 2025'."""
    try:
        y, m, d = (int(x) for x in str(iso)[:10].split("-"))
        return date(y, m, d).strftime("%b %d, %Y").replace(" 0", " ")
    except (ValueError, TypeError):
        return str(iso or "")


def line(code: str) -> str:
    return LINES.get(code, code)


def state(code: str) -> str:
    return ", ".join(STATES.get(s.strip(), s.strip()) for s in str(code).split(","))


def target(t: str) -> str:
    k = str(t or "").split(":", 1)[-1]
    named = {"MIN:Policy": "Minimum premium", "PCT:Terrorism": "Terrorism",
             "TABLE:ExpectedLossRatio.Factor": "Experience rating expected loss ratio"}
    if str(t) in named:
        return named[str(t)]
    if str(t).startswith("TABLE:"):
        return "ISO table " + k.rsplit(".", 1)[0]
    return TARGETS.get(k, k)


def versus_iso(value, mode: str = "replace") -> str:
    """A multiplier as a change from ISO: 0.942 -> '6% below ISO', 1.789 -> '79% above ISO', 1 -> 'same as ISO'."""
    try:
        v = Decimal(str(value))
    except InvalidOperation:
        return str(value)
    pct = (v - 1) * 100
    r = pct.quantize(Decimal(1)) if abs(pct) >= 1 else pct.quantize(Decimal("0.1"))
    if r == 0:
        return "same as ISO" if mode == "replace" else "no change to ISO's rate"
    word = "above" if r > 0 else "below"
    return f"{abs(r)}% {word} ISO" + ("" if mode == "replace" else "'s own rate")


def scope(sc: dict | None) -> str:
    sc = sc or {}
    if not sc:
        return "every class"
    if "class" in sc:
        return f"class {sc['class']}"
    g = str(sc.get("class_group", ""))
    if "aRated" in g or "a-rated" in g.lower():
        return 'specialty ("a"-rated) classes'
    name = re.sub(r"@v\d+$", "", g)
    name = re.sub(r"^[A-Z]+(-[A-Z]{2})?(-[A-Z]{2})?-", "", name)       # UFG-AL-A -> A
    return f"class group {name}" if name else "a group of classes"


def change(pct, against: str = "ISO") -> str:
    """'28.7' -> 'about 29% higher than ISO'; '-5.8' -> 'about 6% lower than ISO'."""
    try:
        v = Decimal(str(pct))
    except InvalidOperation:
        return ""
    r = v.quantize(Decimal(1))
    if r == 0:
        return f"about the same as {against}"
    return f"about {abs(r)}% {'higher' if r > 0 else 'lower'} than {against}"


def _join(names: list) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _same(rows: list) -> str:
    """Rows of one scope, with rates that share a value said once: 'Wind, hail..., Broad-form perils and All other
    covered perils 228% above ISO'."""
    by: dict = {}
    for r in rows:
        by.setdefault(versus_iso(r["value"], r.get("mode", "replace")), []).append(target(r["target"]))
    parts = [f"{_join([ts[0]] + [t[0].lower() + t[1:] for t in ts[1:]])} {v}" for v, ts in by.items()]
    return "; ".join(parts)


def _money(v) -> str:
    d = Decimal(str(v))
    return f"${d:,.0f}" if d == d.to_integral_value() else f"${d:,.2f}"


def _pct(v) -> str:
    return format((Decimal(str(v)) * 100).normalize(), "f") + "%"


def item(r: dict) -> str | None:
    """B-21: a policy-wide item, or a table row with a meaning of its own, as one sentence; None for the rest."""
    t, v = str(r.get("target", "")), r.get("value")
    if t == "MIN:Policy":
        return f"Minimum premium {_money(v)} per policy."
    if t == "PCT:Terrorism":
        return f"Terrorism is charged at {_pct(v)} of the property premium when the coverage is taken."
    if t == "TABLE:ExpectedLossRatio.Factor" and r.get("mode", "replace") == "replace":
        return f"Experience rating uses an expected loss ratio of {_pct(v)} (ISO's is 100%)."
    return None


def row_change(r: dict) -> str:
    """One row's value as the rows table shows it: against ISO for a multiplier, as itself for a B-21 item."""
    t, v = str(r.get("target", "")), r.get("value")
    if t == "MIN:Policy":
        return f"{_money(v)} per policy"
    if t == "PCT:Terrorism":
        return f"{_pct(v)} of the property premium"
    if t == "TABLE:ExpectedLossRatio.Factor" and r.get("mode", "replace") == "replace":
        return f"{_pct(v)} (ISO's is 100%)"
    return versus_iso(v, r.get("mode", "replace"))


def company_rows(rows: list) -> str:
    """A version's rows as plain sentences: the rates for every class (or "all other classes" when groups have their
    own), then each group, e.g. 'Premises and operations 6% below ISO; Products and completed work 79% above ISO.
    Specialty ("a"-rated) classes stay at ISO's rate.' Policy-wide items (a minimum premium, terrorism as a share of
    premium) and the expected loss ratio follow, one sentence each."""
    items = [x for x in (item(r) for r in rows) if x]
    rows = [r for r in rows if item(r) is None]
    base = [r for r in rows if not (r.get("scope") or {})]
    groups: dict = {}
    for r in rows:
        if r.get("scope"):
            groups.setdefault(scope(r.get("scope")), []).append(r)
    real = [g for g in groups if not g.startswith("specialty")]
    out = []
    if base:
        out.append(("All other classes: " if real else "") + _same(base) + ".")
    for where, rs in groups.items():
        cap = where[0].upper() + where[1:]
        if all(versus_iso(r["value"], r.get("mode", "replace")) == "same as ISO" for r in rs):
            out.append(f"{cap} stay at ISO's rate.")
        else:
            out.append(f"{cap}: {_same(rs)}.")
    return " ".join(out + items)


def in_short(md: str) -> str:
    """The 'In short' paragraph of a filing sheet or log entry (a '## In short' section or a line '**In short:** ...')."""
    m = re.search(r"^##+\s*In short\s*\n+(.+?)(?=\n\s*\n|\n#|\Z)", md or "", flags=re.S | re.M)
    if m:
        return " ".join(m.group(1).split())
    m = re.search(r"^\*\*In short:?\*\*:?\s*(.+?)(?=\n\s*\n|\Z)", md or "", flags=re.S | re.M)
    return " ".join(m.group(1).split()) if m else ""


def problem(p: str) -> str:
    """A packet problem said plainly."""
    rules = [
        (r"already in the store and differs", "This packet changes a document or proposal we already have. Send the "
                                              "change as a new version instead."),
        (r"listed in packet.json but not in the zip", "A document the packet lists is missing from the zip."),
        (r"in the zip but not listed", "The zip holds a file the packet doesn't list."),
        (r"not where a packet keeps things", "The zip has a file in the wrong place."),
        (r"class group .* already defined differently", "A group of classes in this packet doesn't match the one we "
                                                        "already have for this insurer."),
        (r"already pins", "This packet asks for different ISO rates than this insurer already uses here."),
        (r"is new to the store", "This packet names a new insurer or company without saying who it is."),
        (r"not a plain file name", "A file name in the packet isn't allowed."),
    ]
    for pat, text in rules:
        if re.search(pat, p):
            return text
    return p
