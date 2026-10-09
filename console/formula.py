"""The rating worksheet's Formula view: how each premium was computed, as arithmetic with the actual factors.

Built from a rating's graph (`gl_engine.interp.graph.RatingGraph`), never from the rules: each Product or Sum the
engine wrote is shown as the operation applied to the values it read, and **only when that arithmetic reproduces
the engine's own value** (to the rule's rounding). A product may carry a "per $100" (x 0.01) or "per $1,000" scale the
rule applies as a constant. Anything else is shown as "computed from" its inputs, never as a guessed formula.

Read-only and display-only: nothing here rates or changes a rating.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

#: Constants a rule applies inside a product without reading them: (factor, how it reads)
SCALES = ((Decimal(1), ""), (Decimal("0.01"), "÷ 100"), (Decimal("0.001"), "÷ 1,000"), (Decimal(100), "× 100"))
PASS = ("Copy", "Value", "FirstNonNull", "Convert")      # a value carried from one place to another
ARITH = ("Product", "Sum", "Round", "Truncate")           # what the Formula view writes out as arithmetic


def _num(v):
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _tol(value: str) -> Decimal:
    """Half a unit of the value's last written place: what rounding could hide."""
    s = str(value)
    places = len(s.split(".", 1)[1]) if "." in s else 0
    return Decimal(1).scaleb(-places) / 2 + Decimal("1e-9")


def _label(path: str) -> str:
    leaf = path.rsplit("/", 1)[-1]
    rec = path.rsplit("/", 2)[-2] if path.count("/") >= 2 else ""
    if leaf in ("Premium", "ErcCalculatedTotalPremium", "Rate", "Factor") and rec:
        rec = re.sub(r"^CommercialProperty|^GeneralLiability", "", rec) or rec
        return f"{rec} {('Total premium' if leaf == 'ErcCalculatedTotalPremium' else leaf)}"
    return leaf


def _rounded_step(nz: list, val: Decimal, tol: Decimal):
    """A product the rule rounds part-way: some factors multiplied and rounded to 3 places, then the rest.
    (ids of the inner factors, the rounded inner value, the final unrounded result), or None."""
    from decimal import ROUND_HALF_UP
    from itertools import combinations
    vals = [(s, v) for s, v in nz if v != 1]
    if not 3 <= len(vals) <= 8:
        return None
    fits = []
    for size in range(2, len(vals)):
        for inner in combinations(range(len(vals)), size):
            a = Decimal(1)
            for i in inner:
                a *= vals[i][1]
            a = a.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            rest = a
            for i in range(len(vals)):
                if i not in inner:
                    rest *= vals[i][1]
            if abs(rest - val) <= tol:
                fits.append(([vals[i][0] for i in inner], a, rest))
    if not fits:
        return None
    return fits[0] + (len(fits),)


#: What may be added to a product: a charge or premium, never a factor, rate or multiplier (those only multiply)
_NOT_ADDABLE = re.compile(r"Factor|Multiplier|LCM|Indicator|(Rate|Mod|Modification|ModToUse|ILF|ELP)$")


def _mixed(ins: list, val: Decimal, tol: Decimal, addable=lambda gid: True):
    """A product of some inputs (with any scale) plus the rest: (ids in the product, scale, exact result), or None.
    Only inputs that are charges or premiums may be the added part (`addable`)."""
    from itertools import combinations
    idx = [i for i, (_, v) in enumerate(ins) if v != 0]
    if not 3 <= len(idx) <= 9:
        return None
    for size in range(len(idx) - 1, 1, -1):
        for grp in combinations(idx, size):
            if not all(addable(ins[i][0]) for i in idx if i not in grp):
                continue
            prod = Decimal(1)
            for i in grp:
                prod *= ins[i][1]
            rest = sum((ins[i][1] for i in idx if i not in grp), Decimal(0))
            for k, how in SCALES:
                if abs(prod * k + rest - val) <= tol:
                    return [ins[i][0] for i in grp], how, prod * k + rest
    return None


class Formulas:
    def __init__(self, graph, affected: set | None = None):
        self.g = graph
        self.aff = affected or set()

    # ---------------------------------------------------------------- nodes
    def _through(self, gid: int) -> int:
        """Follow pure carries (a Copy of one value) to where the value was made."""
        seen = set()
        while gid not in seen:
            seen.add(gid)
            n = self.g.nodes[gid]
            if n["kind"] != "write" or n.get("op") not in PASS:
                return gid
            src = [s for s, k in self.g.parents(gid) if k == "data"]
            if len(src) != 1:
                return gid
            nxt = self.g.nodes[src[0]]
            if _num(nxt.get("value")) is None or _num(nxt.get("value")) != _num(n.get("value")):
                return gid
            gid = src[0]
        return gid

    def describe(self, gid: int) -> dict:
        """One term: its name, value, and where it came from."""
        g, n = self.g, self.g.nodes[gid]
        out = {"id": gid, "value": n.get("value"), "affected": gid in self.aff}
        if n["kind"] == "table":
            out.update(name=f"{n['table']}", source="table", detail=f"{n['table']}[{', '.join(n.get('keys') or [])}]."
                       f"{n['column']}" + (" (carrier's own table row)" if n.get("company") else ""))
        elif n["kind"] == "company":
            out.update(name=n.get("label") or "carrier source", source="filing", detail=n.get("explain") or "")
        elif n["kind"] == "input":
            out.update(name=_label(n.get("path") or ""), source="input", detail="from the request")
        else:
            out["name"] = _label(n.get("path") or "")
            tabs = [s for s, k in g.parents(gid) if k == "data" and g.nodes[s]["kind"] == "table"]
            if n.get("op") in ARITH:
                out["source"] = "formula"
            elif tabs:
                t = g.nodes[tabs[-1]]
                out.update(source="table", detail=f"{t['table']}[{', '.join(t.get('keys') or [])}].{t['column']}"
                           + (" (carrier's own table row)" if t.get("company") else ""))
            elif n.get("op") == "Constant":
                out.update(source="constant", detail="set by the rule")
            else:
                out.update(source="rule", detail=f"{n.get('op') or 'rule'} in {n.get('rule') or 'the rules'}")
        return out

    def _addable(self, gid: int) -> bool:
        n = self.g.nodes[gid]
        leaf = (n.get("path") or n.get("table") or n.get("label") or "").rsplit("/", 1)[-1]
        return n["kind"] != "company" and not _NOT_ADDABLE.search(leaf)

    # ---------------------------------------------------------------- formulas
    def formula(self, gid: int) -> dict:
        """The arithmetic behind one written value, checked against it."""
        gid = self._through(gid)
        n, g = self.g.nodes[gid], self.g
        me = self.describe(gid)
        if n["kind"] != "write" or n.get("op") not in ARITH:
            return {**me, "op": None}
        val = _num(n.get("value"))
        ins = []
        for s, k in g.parents(gid):
            if k != "data":
                continue
            s2 = self._through(s)
            v = _num(g.nodes[s2].get("value"))
            if v is None:
                continue
            ins.append((s2, v))
        # one term per distinct source (a value read twice is one factor)
        uniq = {}
        for s, v in ins:
            uniq.setdefault(s, v)
        ins = list(uniq.items())
        out = {**me, "op": n["op"], "terms": [], "omitted": [], "checks": False}
        if val is None or not ins:
            return out
        tol = _tol(n["value"])
        if n["op"] in ("Round", "Truncate"):
            # the step itself rounds: to whole units, or to the places it wrote
            tol = Decimal("0.5") + Decimal("1e-9") if "." not in str(n["value"]) else tol
            out["op"] = "Product" if len(ins) > 1 else "Sum"
            if len(ins) == 1:
                out.update(terms=[self.describe(ins[0][0])], checks=abs(ins[0][1] - val) <= tol,
                           exact=str(ins[0][1]), rounded=ins[0][1] != val)
                return out
            mixed = _mixed(ins, val, tol, self._addable)
            if mixed:
                return self._mixed_out(out, ins, mixed, val)
        if n["op"] == "Sum":
            total = sum((v for _, v in ins), Decimal(0))
            used = [(s, v) for s, v in ins if v != 0]
            out["omitted"] = [self.describe(s) for s, v in ins if v == 0]
            if abs(total - val) <= tol:
                out.update(terms=[self.describe(s) for s, _ in used], checks=True, exact=str(total))
            else:
                out.update(terms=[self.describe(s) for s, _ in ins], note="these are its inputs; the rule combines "
                           "them in a way this view doesn't reconstruct")
            return out
        # Product: the non-neutral factors, and any scale the rule applies
        if val == 0 and any(v == 0 for _, v in ins):
            zero = [s for s, v in ins if v == 0]
            out.update(checks=True, exact="0", terms=[self.describe(s) for s in zero[:1]],
                       note="0, because this factor is 0 (nothing to charge here)")
            out["rounded"] = False
            return out
        nz = [(s, v) for s, v in ins if v != 0]
        prod = Decimal(1)
        for _, v in nz:
            prod *= v
        for k, how in SCALES:
            if abs(prod * k - val) <= tol:
                out.update(checks=True, scale=how, exact=str((prod * k).normalize()))
                break
        if not out["checks"]:
            got = _rounded_step(nz, val, tol)
            if got:
                inner, rounded, exact, n_fits = got
                note = ("the rule rounds this part to 3 places before applying the rest" if n_fits == 1 else
                        "the rule rounds part-way to 3 places; this is one grouping that reproduces its figure "
                        f"({n_fits} do), so the exact order of the rounding isn't certain")
                out.update(checks=True, exact=str(exact.normalize()),
                           step={"ids": inner, "value": str(rounded), "note": note})
        if out["checks"]:
            out["terms"] = [self.describe(s) for s, v in nz if v != 1]
            out["neutral"] = [self.describe(s) for s, v in nz if v == 1]
            out["omitted"] = [self.describe(s) for s, v in ins if v == 0]
            if len(nz) < len(ins):
                out["zeroNote"] = "added terms that are 0 here (surcharges that don't apply) are left out"
        else:
            mixed = _mixed(ins, val, tol, self._addable)
            if mixed:
                return self._mixed_out(out, ins, mixed, val)
            out.update(terms=[self.describe(s) for s, _ in ins], note="these are its inputs; the rule combines them "
                       "in a way this view doesn't reconstruct")
        out["rounded"] = out.get("exact") is not None and _num(out["exact"]) != val
        return out

    def _mixed_out(self, out: dict, ins: list, mixed: tuple, val: Decimal) -> dict:
        """(a × b ÷ 1,000) + c: a product of some inputs, plus the others."""
        prod_ids, how, exact = mixed
        ids = set(prod_ids)
        prod = [s for s, v in ins if s in ids and v != 1]
        add = [s for s, v in ins if s not in ids and v != 0]
        out.update(op="Mixed", checks=True, exact=str(exact.normalize()), scale=how,
                   terms=[self.describe(s) for s in prod] + [self.describe(s) for s in add],
                   mixed={"product": prod, "add": add},
                   neutral=[self.describe(s) for s, v in ins if s in ids and v == 1],
                   omitted=[self.describe(s) for s, v in ins if s not in ids and v == 0])
        out["rounded"] = _num(out["exact"]) != val
        return out

    def premiums(self, prefix_paths: list[str] | None = None) -> dict:
        """The policy's total premium, as the first formula to open."""
        tops = sorted((p for p in self.g.final if p.endswith("/ErcCalculatedTotalPremium")), key=lambda p: p.count("/"))
        if not tops:
            tops = sorted((p for p in self.g.final if p.endswith("Premium")), key=lambda p: p.count("/"))
        return {"top": self.g.final[tops[0]] if tops else None, "path": tops[0] if tops else None}


# --------------------------------------------------------------------- the worksheet's Formula view

_WORDS = ((r"ErcCalculatedTotalPremium", "Total premium"), (r"PrsnlProp", "Personal Property "),
          (r"BasicGroupII", "Group II "), (r"BasicGroupI", "Group I "), (r"BGII", "Group II "), (r"BGI", "Group I "),
          (r"LOI", "Limit Of Insurance "), (r"BCEG", "BCEG "), (r"IRPM", "IRPM "), (r"Coverage(?= ›|$)", ""),
          (r"CommercialProperty|GeneralLiability", ""))


def pretty(label: str) -> str:
    """'BuildingBasicGroupICoverage › Premium' -> 'Building Group I › Premium': the worksheet's names, readable."""
    out = []
    for part in label.split(" › "):
        for a, b in _WORDS:
            part = re.sub(a, b, part)
        part = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", part)
        part = re.sub(r"\s+", " ", part).strip()
        if part:
            out.append(part[0].upper() + part[1:])
    return " › ".join(out) or label


_ORDER = {"input": 0, "formula": 1, "table": 2, "rule": 3, "constant": 4, "filing": 5}

def tree(graph, affected: set | None = None, label=None, item=None, max_nodes: int = 400) -> dict:
    """The policy's total premium as nested formulas, down to table rows, inputs and filing rows.

    A step that only passes one value along (a total of one total) is skipped, so each line is real arithmetic.
    A value already shown higher up is referred to, not repeated."""
    F = Formulas(graph, affected)
    top = F.premiums()["top"]
    if top is None:
        return {"error": "no premium in this rating"}
    shown, count = set(), [0]

    def name(t: dict) -> dict:
        n = graph.nodes[t["id"]]
        if n.get("path") and label:
            t["name"] = pretty(label(n["path"]))
            t["item"] = item(n["path"]) if item else ""
            if t["name"].lower().endswith("premium"):
                # a premium is named for what it covers: "Business income Group I premium", "Building total premium"
                short = (t["item"].split(" › ")[-1] if t["item"] else "").strip()
                nm = t["name"].replace(" › Premium", " premium").replace("Total premium", "total premium")
                if short and short != "Policy" and not nm.lower().startswith(short.lower()):
                    nm = f"{short} {nm}"
                t["name"] = nm[0].upper() + nm[1:]
        elif n["kind"] == "company":
            t["name"] = pretty(t.get("name") or "LCM").replace(" LCM", " LCM (filing)")
        return t

    def skip(gid: int) -> int:
        for _ in range(50):
            f = F.formula(gid)
            if f.get("op") and f["checks"] and len(f["terms"]) == 1 and not f.get("scale") and not f.get("step") \
                    and _num(f["terms"][0]["value"]) == _num(f["value"]):
                gid = f["terms"][0]["id"]
                continue
            return f["id"] if f.get("id") is not None else gid
        return gid

    def build(gid: int, depth: int = 0) -> dict:
        gid = skip(gid)
        f = F.formula(gid)
        name(f)
        if f.get("op") is None or f["id"] in shown or count[0] >= max_nodes or depth > 30:
            if f["id"] in shown and f.get("op"):
                f["seeAbove"] = True
            f.pop("terms", None)
            return f
        shown.add(f["id"])
        count[0] += 1
        f["terms"] = sorted((build(t["id"], depth + 1) for t in f["terms"]),
                            key=lambda t: _ORDER.get("formula" if t.get("op") else t.get("source"), 3))
        for k in ("neutral", "omitted"):
            f[k] = [name(x) for x in f.get(k, [])]
        return f

    root = build(top)
    root["name"] = "Policy total premium"
    return {"root": root, "count": count[0]}
