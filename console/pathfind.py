"""Scenarios for one Coverage Board cell: which risks walk this path in this state (the user's ask, 2026-10-07).

A path is known only from a rating's trace (`signature`), so the search rates candidates on our engine, free, and keeps
those that walk it. Candidates: the state's base risk, the quick smoke risk, then one control changed at a time, the
controls and values whose words best match the path's label first; then the same changes on the smoke risk. It stops at
`want` hits or `seconds`, and says how many it tried -- a path no single control reaches (a company ELP, a specific
rate) honestly comes back empty. Nothing here spends a call; sending what it found is a plan (`plans.commit`).
"""
from __future__ import annotations

import re
import time

from . import catalog as C, paths as PA, presets, workbench as WB

STOP = {"and", "the", "of", "per", "a", "in", "d8", "d9", "d10", "d11", "filed", "at", "zero", "0", "incl", "other",
        "than", "class", "rated", "rate", "limit", "mechanism", "replaces"}
SYN = {"prem/ops": ["premops", "premises"], "prod/co": ["prods", "products"], "bi/pd": ["bipd"],
       "occurrence": ["occurrence"], "claim": ["claim"], "cov": [], "c": ["medical"], "b": [], "ilf": ["limit"],
       "sor": ["size"], "%": ["%"], "wind/hail": ["wind", "hail"], "bpp": ["bpp", "personal"],
       "bldg": ["bldg", "building"], "bi": ["bi"], "claims-made": ["claims", "made"], "2027": ["2027"],
       "units": ["units"], "area": ["area"], "payroll": ["payroll"], "sales": ["sales"], "bceg": ["bceg"],
       "coinsurance": ["coinsurance"], "broad": ["broad"], "special": ["special"], "basic": ["basic"]}
VALUES_PER_CONTROL = 12


def _words(text: str) -> set:
    out = set()
    for w in re.findall(r"[a-z0-9/%\-]+", text.lower()):
        if w in STOP:
            continue
        out.add(w)
        out.update(SYN.get(w, []))
        out.update(x for x in re.split(r"[/\-]", w) if x and x not in STOP)
    return out


def _candidates(line: str, state: str, target: set) -> list:
    """[(score, label, config)] one control changed at a time, best match first."""
    out = []
    for d in C.dimensions(line, state):
        vals = list(d.get("values") or [])
        if not vals or d["id"] in ("package_version",):
            continue
        dw = _words(d["id"].replace("_", " ") + " " + d["label"])
        pick = list(dict.fromkeys((d.get("suggested") or []) + list(d.get("edges") or []) +
                                  [v for v in vals if _words(str(v)) & target]))
        rest = [v for v in vals if v not in pick]
        step = max(1, len(rest) // max(1, VALUES_PER_CONTROL - len(pick)))
        pick += rest[::step]
        for v in pick[:max(VALUES_PER_CONTROL, len(pick) if d["id"] == "premium_basis" else 0)]:
            vw = _words(str(v))
            score = 5 * len(vw & target) + min(1, len(dw & target))   # the value says more than the control's name
            out.append((score, f"{d['label']}: {(d.get('labels') or {}).get(v, v)}", {d["id"]: v}))
    out.sort(key=lambda x: -x[0])
    return out


def find(line: str, state: str, path_id: str, want: int = 3, seconds: float = 30.0) -> dict:
    meta = PA.paths(line).get(path_id)
    if not meta:
        return {"error": f"no path {path_id} for {line}"}
    ok, why = PA.applies(line, state, path_id)
    if not ok:
        return {"line": line, "state": state, "path": path_id, "label": meta["label"], "applies": False, "why": why,
                "found": [], "tried": 0, "seconds": 0}
    target = _words(meta["label"])
    smoke = dict(presets.SMOKE_GL if line == "GL" else presets.SMOKE_CP)
    cands = [(99, "The state's base risk", {}), (98, "The quick smoke risk (retail)", smoke)]
    singles = _candidates(line, state, target)
    cands += singles + [(s - 0.5, f"Quick smoke risk, {lab[0].lower() + lab[1:]}", {**smoke, **cfg})
                        for s, lab, cfg in singles]
    t0, tried, found, seen = time.time(), 0, [], set()
    for _, label, cfg in cands:
        el = time.time() - t0
        if len(found) >= want or el > seconds or (found and el > 12):   # one in hand: don't hold the screen for more
            break
        try:
            req = C.build(line, state, cfg)
        except Exception:                                     # noqa: BLE001 -- not declarable here: not a candidate
            continue
        tried += 1
        r = WB.rate(line, req)
        if r.get("outcome") != "rated" or path_id not in (r.get("paths") or []):
            continue
        key = (r.get("premium"), tuple(r.get("paths") or []))
        if key in seen:                                        # the same rating by another route adds nothing
            continue
        seen.add(key)
        found.append({"label": label, "config": cfg, "premium": r.get("premium"), "paths": r.get("paths"),
                      "stored": r.get("stored"), "hash": r.get("hash"),
                      "classification": r.get("classification")})
    return {"line": line, "state": state, "path": path_id, "label": meta["label"], "applies": True,
            "found": found, "tried": tried, "seconds": round(time.time() - t0, 1),
            "exhausted": len(found) < want and time.time() - t0 <= seconds}
