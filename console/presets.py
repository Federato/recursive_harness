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


def _all_gl() -> list:
    import variants as V
    return sorted(V.Declared.jurisdictions())


def presets() -> list:
    """[{id, name, what, line, spec}] for every tier and layer that needs no further input."""
    import qa
    import layers as L
    out = []
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
