"""What changed between two versions of a filing, or between a filing and ISO."""
from __future__ import annotations

import json
from decimal import Decimal

from . import iso
from .files import Filing
from .validate import Report

#: Where ISO keeps the LCM a filing's `LCM:` rows stand in for, per target.
_ISO_LCM = {
    "CF": {t: ("LossCostMultiplier", "Factor")
           for t in ("GroupI", "GroupII", "Broad", "Special", "Earthquake")},
    "GL": {"PremOps": ("PremOpsLCM", "Rate"),
           "ProdsCompldOps": ("ProdsCompldOpsLCM", "Rate")},
}


def _key(row) -> str:
    return row.target + " " + json.dumps(row.scope, sort_keys=True, default=str)


def diff_versions(a: Filing, b: Filing) -> list[str]:
    out = []
    for k in ("new_eff", "renewal_eff", "juris", "status", "approved", "opt_out"):
        if a.raw.get(k) != b.raw.get(k):
            out.append(f"~ {k}: {a.raw.get(k)!r} -> {b.raw.get(k)!r}")
    ra = {_key(r): r for r in a.rows}
    rb = {_key(r): r for r in b.rows}
    for k in ra.keys() - rb.keys():
        out.append(f"- {k} = {ra[k].value} ({ra[k].mode})")
    for k in rb.keys() - ra.keys():
        out.append(f"+ {k} = {rb[k].value} ({rb[k].mode})")
    for k in sorted(ra.keys() & rb.keys()):
        x, y = ra[k], rb[k]
        if (x.value, x.mode) != (y.value, y.mode):
            out.append(f"~ {k}: {x.value} ({x.mode}) -> {y.value} ({y.mode})")
    return out or ["no differences"]


def diff_iso(rep: Report) -> list[str]:
    """Per jurisdiction and table: how far the company's values sit from ISO's."""
    f = rep.filing
    out = []
    for j, (ctx, exps, composed, ed_new, _) in rep.plans.items():
        out.append(f"{j}  ISO {ed_new['state']} over {ed_new['countrywide']}")
        for space, keys in sorted(composed.items()):
            if space[0] == "LCM":
                for tgt, (tname, col) in _ISO_LCM[f.line].items():
                    vals = [c for k, c in keys.items() if k[0] == tgt]
                    if not vals:
                        continue
                    t = iso.table(f.line, j, ctx.date, tname)
                    ci, si = t.col(col), t.col("StateCode")
                    isov = next((r[ci] for r in t.rows if r[si] == j),
                                next((r[ci] for r in t.rows), None))
                    lo = min(_final(c, isov) for c in vals)
                    hi = max(_final(c, isov) for c in vals)
                    out.append(f"  LCM {tgt:<15} ISO {isov}  company {lo}"
                               + (f" to {hi}" if hi != lo else "") + f"  ({len(vals)} keys)")
            elif space[0] == "POLICY":
                # OI-142: a policy item (B-21 `MIN:Policy`) has no ISO table; ISO files no such value.
                for c in keys.values():
                    out.append(f"  {space[1]:<19} ISO none  company {c.value} ({c.mode})")
            else:
                _, tname, col = space
                t = iso.table(f.line, j, ctx.date, tname)
                kn = iso.table_keys(t)
                idx = [t.col(k) for k in kn]
                ci = t.col(col)
                isomap = {tuple(str(r[i]) for i in idx): r[ci] for r in t.rows}
                out.append(f"  {tname}.{col} from {t.package}")
                for k, c in sorted(keys.items()):
                    isov = isomap.get(k)
                    out.append(f"    {'/'.join(k):<40} ISO {isov}  company {_final(c, isov)}")
    return out


def _final(c, isov) -> Decimal:
    if c.mode == "replace" or isov is None:
        return c.value
    return Decimal(str(isov)) * c.value
