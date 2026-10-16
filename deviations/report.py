"""The `Deviation` block a carrier rating carries beside its ISO-shaped tree (§3c).

Shared by both lines. The caller supplies two rated trees (technical and carrier), their premiums, and a way to
re-rate under a reduced plan, which is how the waterfall attributes the difference one step at a time.

**The waterfall's order is fixed** (plan v2 fix): LCM, then each overridden ISO table in name
order, then the policy-level items in the order they apply (B-21: terrorism as a share of premium, then the policy
minimum). Multiplied effects depend on order, so a fixed order is what makes the breakdown repeatable. The last
step, "rounding left over", is carrier minus everything before it; with cumulative steps it is zero by
construction, and a non-zero value there means a step could not be rated.
"""
from __future__ import annotations

from decimal import Decimal


def _num(v) -> Decimal | None:
    try:
        return Decimal(str(v))
    except Exception:
        return None


def _leaves(node, prefix: str = "", out: dict | None = None) -> dict:
    out = {} if out is None else out
    seen: dict = {}
    for c in node.children:
        i = seen.get(c.tag, 0)
        seen[c.tag] = i + 1
        p = f"{prefix}/{c.tag}[{i}]"
        if c.children:
            _leaves(c, p, out)
        elif c.text not in (None, ""):
            out[p] = c.text
    return out


def _same(a, b) -> bool:
    x, y = _num(a), _num(b)
    return x == y if x is not None and y is not None else str(a) == str(b)


#: Fields each side mints for itself and that never compare (identifiers).
_MINTED = ("Guid", "Id")


def changed_paths(technical, carrier, lcm_field: str) -> list:
    """Every field whose value differs between the technical and carrier trees."""
    t, c = _leaves(technical), _leaves(carrier)
    out = []
    for p in sorted(set(t) | set(c)):
        a, b = t.get(p), c.get(p)
        name = p.rsplit("/", 1)[-1].split("[")[0]
        if name.endswith(_MINTED) or a == b or (a is not None and b is not None and _same(a, b)):
            continue
        row = {"path": p, "iso": a, "carrier": b}
        if name == lcm_field:
            row["row"] = "company LCM"
        out.append(row)
    return out


def build(plan, edition: str, technical_premium, carrier_premium, technical_tree, carrier_tree,
          rerun, waterfall: bool = True) -> dict:
    """`rerun(reduced_plan)` -> premium."""
    from .engine import LCM_FIELD
    tp, cp = _num(technical_premium), _num(carrier_premium)
    m = plan.manifest
    dev = {"writingCompany": plan.company, "policyType": plan.policy_type,
           "edition": edition,
           "filings": ([{"id": m["filing"], "version": m["version"], "new_eff": m["new_eff"],
                         "renewal_eff": m["renewal_eff"]}] if m else []),
           "technicalPremium": technical_premium, "carrierPremium": carrier_premium}
    steps = []
    if waterfall and tp is not None and cp is not None:
        from .engine import POLICY_ORDER, policy_label
        prev = tp
        order = ((["LCM"] if plan.group_lcm or plan.lcm else []) + sorted(plan.overrides)
                 + [k for k in POLICY_ORDER if k in plan.policy])
        for i, name in enumerate(order):
            rest = order[i + 1:]
            v = cp if not rest else _num(rerun(plan.without(
                lcm="LCM" in rest, tables=[t for t in rest if t in plan.overrides],
                policy=[t for t in rest if t in plan.policy])))
            if v is not None:
                steps.append({"step": policy_label(plan, name) if name in plan.policy else name,
                              "effect": str(v - prev)})
                prev = v
        steps.append({"step": "rounding left over", "effect": str(cp - prev)})
    dev["waterfall"] = steps
    dev["changedPaths"] = (changed_paths(technical_tree, carrier_tree, LCM_FIELD[plan.line])
                           if technical_tree is not None and carrier_tree is not None else [])
    dev["warnings"] = list(plan.warnings)
    return dev
