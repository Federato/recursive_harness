"""Starting points for a test plan (TC-36 parity: `/tester`'s QA tiers, T1, and `/tests`' layers, L1).

The tiers and layers stay defined where they always were (`scripts/qa.py`, `scripts/layers.py`); this only turns each
into a plan spec: its states and its explicit scenarios (`configs`), which the Test Plan Builder can extend with
pairwise dimensions, thin with an allowance, and commit. Nothing here rates or spends.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.append(str(ROOT / "scripts"))


#: Quick smoke (the user's ask, 2026-10-07): one retail risk per state at industry-standard selections, GL and
#: Property. GL: ISO class 11127 (Clothing or Wearing Apparel Stores), $1,000,000 gross sales, premises/operations and
#: products/completed operations together, $1M occurrence / $2M general and products aggregates, occurrence form, no
#: deductibles. Property: ISO class 0567 (Mercantile NOC, sole occupant, moderate-susceptibility personal property,
#: 15,000 sq ft or less), Special causes of loss -- which rates all three of Basic Group I, Basic Group II and Special --
#: joisted masonry, 1-3 stories, $1,000,000 building and $250,000 personal property at 80% coinsurance, replacement
#: cost, $1,000 deductible; the state's sample location (territories, protection class) and business income.
SMOKE_GL = {"subline": "Premises/Operations and Products/Completed Operations", "class_code": "11127",
            "exposure": 1000000, "occurrence_limit": "1,000,000 CSL", "general_aggregate": "2,000,000 CSL",
            "coverage_form": "Occurrence"}
SMOKE_CP = {"cause_of_loss": "Special", "occupancy": "Mercantile", "class_code": "0567",
            "construction": "Joisted Masonry - Other Than Reinforced", "stories": "1-3", "bldg_coinsurance": "80%",
            "bpp_coinsurance": "80%", "bldg_deductible": "1,000", "valuation": "Replacement Cost",
            "bldg_limit": "1000000", "bpp_limit": "250000"}


def _all_cp() -> list:
    import property_rating as pr
    return sorted(pr.states())


def smoke() -> list:
    """The two quick smoke plans: one scenario per state, each line."""
    return [
        {"id": "smoke-gl", "name": "Quick smoke · GL retail (one per state)", "line": "GL",
         "what": "Class 11127 clothing store, $1M gross sales, premises and products, 1M/2M/2M occurrence, no deductible",
         "spec": {"line": "GL", "states": _all_gl(), "dims": {}, "configs": [dict(SMOKE_GL)], "edges": False}},
        {"id": "smoke-cp", "name": "Quick smoke · Property retail (one per state)", "line": "CP",
         "what": "Class 0567 mercantile, Special form (Basic Group I, Basic Group II and Special), joisted masonry, "
                 "$1M building, $250K personal property, 80% coinsurance, replacement cost, $1,000 deductible",
         "spec": {"line": "CP", "states": _all_cp(), "dims": {}, "configs": [dict(SMOKE_CP)], "edges": False}},
    ]


def _all_gl() -> list:
    import variants as V
    return sorted(V.Declared.jurisdictions())


def presets() -> list:
    """[{id, name, what, line, spec}] for every tier and layer that needs no further input."""
    import qa
    import layers as L
    out = smoke()
    for tid in ("T0", "T1", "T2", "T4"):
        t = qa.TIERS[tid]
        sc = qa.scenarios_for(tid)
        states = sorted({j for _, js in sc for j in js}) or _all_gl()
        configs = [dict(c) for c, _ in sc]
        out.append({"id": f"qa-{tid}", "name": f"QA {tid} · {t['name']}", "what": t["what"], "line": "GL",
                    "spec": {"line": "GL", "states": states, "dims": {}, "configs": configs, "edges": False}})
    for lid in ("L1", "L3", "L4"):
        lay = L.LAYERS[lid]
        out.append({"id": f"layer-{lid}", "name": f"Layer {lid} · {lay['name']}", "what": lay["what"], "line": "GL",
                    "spec": {"line": "GL", "states": _all_gl(), "dims": {}, "configs": L._configs(lid), "edges": False}})
    out.append({"id": "layer-L3-reduced", "name": "Layer L3 · Limits (reduced)", "what": "corners and centre of the limits grid",
                "line": "GL", "spec": {"line": "GL", "states": _all_gl(), "dims": {}, "configs": L._configs("L3", "reduced"),
                                       "edges": False}})
    return out
