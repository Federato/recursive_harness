"""Dropdown specifications, from ISO's declaration, cached because it is slow.

The page needs, for every control: a label, why it exists, and **every value
legal anywhere with the list of jurisdictions that declare it**. Building that
means resolving 51 rulebooks and reading their domain tables -- about seven
seconds. Once per as-of date is fine; once per page load is not.

**The cache is derived from licensed ISO content and must never be committed.**
It holds declared class codes, deductible amounts and limit values. `.gitignore`
excludes `ui/cache/`; if that entry is ever lost, this file's contents are the
kind of thing the repository exists to keep out.

Nothing here decides legality. It asks `variants.union_options`, which asks
`gl_engine.schema.Schema`, which reads ISO's domain tables.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import variants as V                                          # noqa: E402

CACHE = Path(__file__).resolve().parent / "cache"

_MEM: dict = {}


def _cache_file(asof: str) -> Path:
    return CACHE / f"options-{asof}.json"


def _controls_fingerprint() -> str:
    """What the cache was built from, so a stale one can be recognised.

    **A cache that survives a change to the thing it caches is worse than no
    cache.** Adding the `classifications` control on 2026-08-17 left this file
    serving 19 controls while the code declared 20, and the only reason it was
    noticed is that `verify_tester` G2 compares the served spec against
    `V.CONTROLS` rather than against a number. The fingerprint turns that from a
    caught mistake into one that cannot happen.
    """
    ids = "|".join(f"{c.id}:{c.kind}:{c.group}" for c in V.CONTROLS)
    return hashlib.sha256(ids.encode()).hexdigest()[:12]


def build(asof: str = V.DEFAULT_ASOF, save: bool = True) -> dict:
    """Resolve every jurisdiction and describe every control. Slow on purpose."""
    t0 = time.time()
    union = V.union_options(asof=asof)
    spec = {
        "asof": asof,
        "controls_fingerprint": _controls_fingerprint(),
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "built_in_seconds": round(time.time() - t0, 1),
        "jurisdictions": union["jurisdictions"],
        "unresolvable": union["failed"],
        "groups": list(V.GROUPS),
        "controls": [
            {
                "id": c.id,
                "label": c.label,
                "group": c.group,
                "exercises": c.exercises,
                "note": c.note,
                "kind": c.kind,
                "cast": c.cast,
                "keyed_by": list(c.keyed_by),
                "unit_from": c.unit_from,
                **union["controls"][c.id],
            }
            for c in V.CONTROLS
        ],
    }
    if save:
        CACHE.mkdir(parents=True, exist_ok=True)
        _cache_file(asof).write_text(json.dumps(spec), encoding="utf-8")
    return spec


def specs(asof: str = V.DEFAULT_ASOF, refresh: bool = False) -> dict:
    """The cached specification, built on first use."""
    if not refresh and asof in _MEM:
        return _MEM[asof]
    f = _cache_file(asof)
    if not refresh and f.exists():
        try:
            spec = json.loads(f.read_text(encoding="utf-8"))
            if spec.get("controls_fingerprint") == _controls_fingerprint():
                _MEM[asof] = spec
                return spec
            # Built from a different control set. Rebuild rather than serve a
            # spec the code no longer agrees with.
        except ValueError:
            pass                       # rebuild rather than serve a torn cache
    spec = build(asof)
    _MEM[asof] = spec
    return spec


def for_juris(juris: str, config: dict | None = None,
              asof: str = V.DEFAULT_ASOF) -> dict:
    """One jurisdiction's own options, given the answers so far.

    This is the exact set -- the union is for populating a dropdown before a
    jurisdiction is chosen; this is what that jurisdiction will actually accept,
    with dependent domains resolved against the current answers.
    """
    d = V.Declared(juris, asof)
    return {
        "juris": juris,
        "territories": list(d.territories()),
        "terrorism_place": list(d.terrorism_place() or ()),
        "controls": V.options_for(d, config or {}),
    }


def legality(config: dict, asof: str = V.DEFAULT_ASOF) -> dict:
    """Which jurisdictions can express this configuration, and why not.

    **Answered without rating anything**, so the page can say *"this will run in
    31 of 51"* before a run is started rather than after. That distinction --
    cannot be asked here versus disagrees here -- is the one a cross-state
    tester most easily gets wrong.
    """
    ok, no = [], {}
    for j in V.Declared.jurisdictions():
        try:
            d = V.Declared(j, asof)
            V.build(config, d)
            ok.append(j)
        except V.VariantError as exc:
            no[j] = str(exc)
        except Exception as exc:                              # noqa: BLE001
            no[j] = f"{type(exc).__name__}: {exc}"
    return {"applicable": ok, "not_applicable": no,
            "summary": f"{len(ok)} of {len(ok) + len(no)}"}
