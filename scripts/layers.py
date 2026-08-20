"""The layered test programme: four layers, an allowance, and a ticker.

    python scripts/layers.py --layers                       # what the layers are
    python scripts/layers.py --layer L2 --class 91340 --exposure 1500000 --plan
    python scripts/layers.py --layer L2 --class 91340 --exposure 1500000 --offline
    python scripts/layers.py --layer L3 --class 91340 --exposure 1500000 \
                             --allowance 200

Sits **beside** `qa.py` rather than inside it. The tier runner (T0-T4) is working
and is being used; this is a different programme with a different unit of work,
and merging the two would have meant editing the one thing nobody asked to
change. They share the run store, the variant definitions and the sweep.

### The ladder, and why that order

Each layer adds exactly one kind of variation, so a difference found at layer *n*
is attributable to what layer *n* introduced.

* **L1 Smoke** -- the base risk, unvaried, everywhere. If this is wrong nothing
  above it means anything.
* **L2 Classification** -- one class code and its exposure, everywhere. The
  engine reads the premium basis from ISO's table for that state; nobody types
  it.
* **L3 Limits** -- occurrence limit against aggregate limit. Two things at once
  and deliberately so: the increased-limit factor is keyed on the pair, and a
  sweep that varies only the occurrence limit tests half a key.
* **L4 Deductibles** -- one amount applied to each of the six slots in turn.
  **The question is which slot is ignored, not what any curve looks like.**
  Mapping a credit curve before knowing every slot reaches the calculation is
  work spent in the wrong order; the amount ladder and the combined-versus-
  separate exclusion are L5 and L6 when this ladder has been walked.

### Every state, every run

There is no promotion step and no sampling of geography. The offline pass runs
first because it is free and it keeps a payload that cannot be built -- or that
our own engine refuses -- from spending a live call. It settles nothing on its
own: **agreement is defined by `phase2_compare.compare_payload` and needs ISO's
actual response**, so an offline pass cannot tell you who is right.

### The allowance, and what it cuts

You set an allowance per run. When the matrix does not fit inside it, **the
config list is thinned and the state list never is.** Every state appears in
every run, so two runs stay comparable; a run that quietly dropped Montana would
make a coverage figure that is not true.

**Which configs survived is recorded in the run.** Two runs of the same layer at
different allowances are different matrices, and one that does not say so
invites a comparison that is not valid.

### The budget is a ticker here, not a gate

`qa.py` weighs a tier against decision A6's standing budget and stops. This does
not: it shows what has been spent today and runs what you asked for. The
programme is now large enough that a gate set for one-day tiers would refuse
most useful runs, and the person holding the subscription is better placed than a
constant is.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sweep                                                   # noqa: E402
import variants as V                                           # noqa: E402
import runstore as store                                       # noqa: E402
from raas import NO_ISO                                        # noqa: E402

#: Measured from the run records, 2026-08-17.
SECONDS_PER_LIVE_CALL = 8.4
SECONDS_PER_OFFLINE_RATING = 0.5

#: The two sublines this programme covers. The stored base submissions are
#: shaped for this family; the other seven need a base of their own.
SUBLINE = "Premises/Operations and Products/Completed Operations"

#: L3's occurrence limits: the default, one either side of it, and the top of
#: the filed table. Chosen to span the increased-limit curve rather than walk
#: it -- the curve's shape is where a keying error shows, not its resolution.
OCCURRENCE_POINTS = ("500,000 CSL", "1,000,000 CSL", "2,000,000 CSL",
                     "5,000,000 CSL")

#: L3's aggregate axis, as **positions rather than figures**. The legal set is
#: keyed on the occurrence limit and differs by state -- four values at 25,000
#: in Texas, eight at 1,000,000 -- so naming a figure would make the run
#: undeliverable wherever that figure is not filed. `resolve` turns a position
#: into that state's value, and the row records what it got.
AGGREGATE_POSITIONS = ("@lowest", "@middle", "@highest")

#: L3's reduced grid -- corners and the center, not the full 4x3 cross.
#: The full grid is 12 configs x 51 jurisdictions = 612 ratings. This is 5 x 51
#: = 255, the nearest full-state design to a ~240-rating target that still
#: varies both axes together, which is the whole point of L3 (see above).
#: Chosen as the two ends of the occurrence axis crossed with the two ends of
#: the aggregate axis, plus the as-filed default (1,000,000 CSL) at
#: @middle. The two interior occurrence points (1,000,000 and 2,000,000 CSL)
#: are dropped from the corners and folded into one center point -- a keying
#: error shows at the ends of a filed curve or not at all; an interior point
#: mostly confirms what the corners already imply. This is a fixed, named
#: subset of the full grid, not a random or evenly-spaced sample of it.
L3_REDUCED = (
    {"occurrence_limit": "500,000 CSL", "general_aggregate": "@lowest"},
    {"occurrence_limit": "500,000 CSL", "general_aggregate": "@highest"},
    {"occurrence_limit": "1,000,000 CSL", "general_aggregate": "@middle"},
    {"occurrence_limit": "5,000,000 CSL", "general_aggregate": "@lowest"},
    {"occurrence_limit": "5,000,000 CSL", "general_aggregate": "@highest"},
)

#: L4's six slots, and the one amount applied to each in turn.
DEDUCTIBLE_SLOTS = ("premops_bi_deductible", "premops_pd_deductible",
                    "premops_bipd_deductible", "prods_bi_deductible",
                    "prods_pd_deductible", "prods_bipd_deductible")
DEDUCTIBLE_AMOUNT = "5,000 Per Occurrence"

LAYERS = {
    "L1": {"name": "Smoke",
           "what": "the base risk, unvaried, in every jurisdiction",
           "varies": "nothing",
           "needs_class": False},
    "L2": {"name": "Classification",
           "what": "one class code and its exposure, in every jurisdiction; "
                   "the premium basis comes from ISO's table per state",
           "varies": "the class code and its exposure",
           "needs_class": True},
    "L3": {"name": "Limits",
           "what": "occurrence limit against aggregate limit, in every "
                   "jurisdiction",
           "varies": "the increased-limit key, both halves of it",
           "needs_class": False},
    "L4": {"name": "Deductibles",
           "what": "one amount applied to each of the six deductible slots in "
                   "turn, in every jurisdiction",
           "varies": "which slot carries a deductible",
           "needs_class": False},
}


class PlanError(RuntimeError):
    """A layer asked for something the declaration cannot supply."""


# --------------------------------------------------------- the basis grouping

def basis_groups(class_code: str, jurisdictions=None,
                 asof: str = V.DEFAULT_ASOF) -> dict:
    """Group jurisdictions by the premium basis ISO files for this class.

    **A guard that will rarely fire, kept because when it fires it matters.**
    Measured across TX, CA, NY, FL, OK and MT: about 1,188 class codes declared
    in each, 1,187 common to all six, and the basis differed for exactly one --
    which was simply undeclared in one state. So a class is almost always one
    group. When it is not, the two groups are measuring different things and a
    premium compared across them is a units artifact, not a rating difference.

    Returns `{"groups": [{basis, jurisdictions}], "undeclared": [...]}`.
    **Undeclared is a result, not a filter.** *ISO does not file this class in
    these states* is a fact about coverage that nothing else in the harness
    reports, and dropping those states silently would turn it into nothing.
    """
    js = list(jurisdictions or V.Declared.jurisdictions())
    by_basis: dict = {}
    undeclared, unreadable = [], {}
    for j in js:
        try:
            d = sweep.declared(j, asof)
        except Exception as exc:                              # noqa: BLE001
            unreadable[j] = f"{type(exc).__name__}: {exc}"[:160]
            continue
        try:
            basis = d.basis_for(str(class_code), "PremOps")
        except V.VariantError:
            undeclared.append(j)
            continue
        by_basis.setdefault(basis, []).append(j)
    groups = [{"basis": b, "jurisdictions": w}
              for b, w in sorted(by_basis.items(), key=lambda kv: -len(kv[1]))]
    return {"groups": groups, "undeclared": undeclared,
            "unreadable": unreadable}


# ------------------------------------------------------------------- the plan

def _configs(layer: str, size: str = "full") -> list:
    """The configurations a layer varies, before a class or a group is applied.

    State-independent by construction: anything that cannot be named the same
    way in all 51 is carried as a position and resolved per state.

    `size` only changes anything for L3 today: "full" is the 4x3 cross
    (~612 ratings), "reduced" is the 5-config corners-plus-center subset
    (~255 ratings, see `L3_REDUCED`). Other layers ignore it -- they have no
    second size defined yet.
    """
    if size not in ("full", "reduced"):
        raise PlanError(f"unknown size {size!r}; known: full, reduced")
    if layer == "L1":
        return [{}]
    if layer == "L2":
        return [{}]                    # the class itself is the variation
    if layer == "L3":
        if size == "reduced":
            return [dict(c) for c in L3_REDUCED]
        return [{"occurrence_limit": occ, "general_aggregate": pos}
                for occ in OCCURRENCE_POINTS for pos in AGGREGATE_POSITIONS]
    if layer == "L4":
        return [{slot: DEDUCTIBLE_AMOUNT} for slot in DEDUCTIBLE_SLOTS]
    raise PlanError(f"unknown layer {layer!r}")


def plan(layer: str, class_code: str = "", exposure=None,
         jurisdictions=None, allowance: int | None = None,
         asof: str = V.DEFAULT_ASOF, offline: bool = False,
         size: str = "full") -> dict:
    """What a run would do, without doing any of it.

    `exposure` may be one number, or `{basis: number}` when a class turns out to
    be filed on different bases in different states and one figure would not
    mean the same thing in both groups.

    **An allowance is denominated in live calls, so it cuts nothing offline.**
    An offline run costs no calls; thinning it to fit a call budget would
    discard coverage to save something it was never going to spend.

    **`size` is a different lever from `allowance`, and does the opposite
    kind of cutting.** An allowance thins the config list for the live pass
    only and records what it dropped; `size="reduced"` shrinks the config
    list itself, before either pass, so the offline run is smaller too. Use
    `size` to run a deliberately smaller, named grid (see `L3_REDUCED`); use
    `allowance` to run the full grid offline and a thinned slice of it live.
    The two compose: a reduced-size run can still be given its own allowance.
    """
    if layer not in LAYERS:
        raise PlanError(f"unknown layer {layer!r}; known: {', '.join(LAYERS)}")
    spec = LAYERS[layer]
    if spec["needs_class"] and not class_code:
        raise PlanError(f"{layer} ({spec['name']}) needs a class code")

    js = list(jurisdictions or V.Declared.jurisdictions())
    if class_code:
        grouping = basis_groups(class_code, js, asof)
        groups = grouping["groups"]
    else:
        # No class named: the base submission's own classification stands, and
        # there is nothing to group by.
        grouping = {"groups": [], "undeclared": [], "unreadable": {}}
        groups = [{"basis": "", "jurisdictions": js}]

    configs = _configs(layer, size)
    scenarios = []
    for cfg in configs:
        for g in groups:
            full = {"subline": SUBLINE}
            full.update(cfg)
            if class_code:
                full["class_code"] = str(class_code)
                amount = _exposure_for(exposure, g["basis"])
                if amount is not None:
                    full["exposure"] = amount
            scenarios.append({
                "config": full,
                "basis": g["basis"],
                "jurisdictions": list(g["jurisdictions"]),
                "describes": describe(full),
            })

    kept = scenarios
    thinning = None
    if allowance is not None and not offline:
        kept, thinning = thin(scenarios, allowance, len(configs), len(groups))

    out = {
        "layer": layer, "name": spec["name"], "what": spec["what"],
        "size": size,
        "class_code": str(class_code), "exposure": exposure,
        "asof": asof,
        "jurisdictions": js,
        "groups": groups,
        "undeclared": grouping["undeclared"],
        "unreadable": grouping["unreadable"],
        "configs_planned": len(configs),
        "scenarios": kept,
        "thinning": thinning,
        "spent_today": store.spent_today(),
        "offline": bool(offline),
    }
    out["cost"] = estimate(kept, offline)
    return out


def _exposure_for(exposure, basis: str):
    if exposure is None:
        return None
    if isinstance(exposure, dict):
        if basis in exposure:
            return exposure[basis]
        return exposure.get("", None)
    return exposure


def describe(config: dict) -> str:
    """`V.describe`, but readable while an aggregate is still a position."""
    c = dict(config)
    pos = c.get("general_aggregate")
    if isinstance(pos, str) and pos.startswith("@"):
        c["general_aggregate"] = f"{pos[1:]} legal aggregate"
    bits = []
    for k in ("class_code", "exposure", "occurrence_limit",
              "general_aggregate"):
        if k in c:
            bits.append(f"{V.BY_ID[k].label}={c[k]}")
    for k in DEDUCTIBLE_SLOTS:
        if k in c:
            bits.append(f"{V.BY_ID[k].label}={c[k]}")
    return ", ".join(bits) or "the base risk, unvaried"


# --------------------------------------------------------------- the thinning

def _spread(n: int, k: int) -> list:
    """`k` indices out of `n`, evenly, always including the first and last.

    The ends of a filed table are where a keying error shows -- the lowest and
    highest limit, the first and last slot. A thinning that kept the middle
    would drop exactly the rows worth having.
    """
    if k >= n:
        return list(range(n))
    if k <= 1:
        return [0]
    step = (n - 1) / (k - 1)
    return sorted({int(round(i * step)) for i in range(k)})


def thin(scenarios: list, allowance: int, n_configs: int, n_groups: int):
    """Fit the matrix inside the allowance by dropping configs, never states.

    Returns `(kept, report)`. The report is stored with the run, because a run
    that was thinned and does not say so cannot be compared with one that was
    not.
    """
    live = sum(len([j for j in s["jurisdictions"] if j not in NO_ISO])
               for s in scenarios)
    if allowance is None or live <= allowance or n_configs <= 1:
        return scenarios, {"applied": False, "live_calls": live,
                           "allowance": allowance,
                           "configs_kept": n_configs,
                           "configs_planned": n_configs, "dropped": []}

    per_config = max(1, live // max(1, n_configs))
    k = max(1, allowance // per_config)
    keep_idx = set(_spread(n_configs, k))
    kept, dropped = [], []
    for i, s in enumerate(scenarios):
        # Scenarios are laid out config-major: config i covers `n_groups` rows.
        (kept if (i // max(1, n_groups)) in keep_idx else dropped).append(s)
    return kept, {
        "applied": True,
        "allowance": allowance,
        "live_calls": sum(len([j for j in s["jurisdictions"]
                               if j not in NO_ISO]) for s in kept),
        "configs_planned": n_configs,
        "configs_kept": len(keep_idx),
        "kept": [s["describes"] for s in kept[:n_groups * len(keep_idx)]],
        "dropped": sorted({s["describes"] for s in dropped}),
        "why": "states are never cut; the config list was thinned to the ends "
               "and an even spread between them",
    }


def estimate(scenarios: list, offline: bool = False) -> dict:
    ratings = sum(len(s["jurisdictions"]) for s in scenarios)
    live = 0 if offline else sum(
        len([j for j in s["jurisdictions"] if j not in NO_ISO])
        for s in scenarios)
    return {"scenarios": len(scenarios), "ratings": ratings,
            "live_calls": live,
            "offline_seconds": round(ratings * SECONDS_PER_OFFLINE_RATING),
            "live_seconds": round(live * SECONDS_PER_LIVE_CALL)}


# ------------------------------------------------------- per-state resolution

def resolve(config: dict, d: V.Declared) -> dict:
    """Turn positions into the values this jurisdiction actually declares.

    Raises `VariantError` when the state declares nothing for the position,
    which `sweep.run_config` reports as `NOT APPLICABLE` -- the third outcome,
    never a failure.
    """
    pos = config.get("general_aggregate")
    if not (isinstance(pos, str) and pos.startswith("@")):
        return config
    occurrence = config.get("occurrence_limit")
    if not occurrence:
        occurrence = (d.base().get("body", {}).get("GeneralLiability", [{}])[0]
                      .get("PremOpsProdsEachOccurrenceLimit"))
    legal = d.aggregates_for(occurrence) if occurrence else ()
    if not legal:
        raise V.VariantError(
            f"{d.juris} declares no aggregate limit legal with an "
            f"each-occurrence limit of {occurrence}")
    if pos == "@lowest":
        value = legal[0]
    elif pos == "@highest":
        value = legal[-1]
    else:
        value = legal[len(legal) // 2]
    out = dict(config)
    out["general_aggregate"] = value
    return out


# ---------------------------------------------------------------- the running

def run(layer: str, class_code: str = "", exposure=None, jurisdictions=None,
        allowance: int | None = None, offline: bool = False,
        asof: str = V.DEFAULT_ASOF, progress=None, stop_check=None,
        label: str = "", scenario_done=None) -> dict:
    """Run a layer. Returns the plan, the stored run ids and a rollup.

    The offline pre-flight is not optional and not a decision point: it runs
    first, costs nothing, and its only job is to keep a payload that cannot be
    built from spending a live call.
    """
    p = plan(layer, class_code, exposure, jurisdictions, allowance, asof,
             offline)
    scenarios = p["scenarios"]
    results, run_ids = [], []
    started = time.time()

    for i, s in enumerate(scenarios, 1):
        if stop_check is not None and stop_check():
            p["stopped_after"] = i - 1
            break
        if progress:
            progress({"phase": "offline", "scenario": i,
                      "of": len(scenarios), "describes": s["describes"]})
        pre = sweep.run_config(s["config"], s["jurisdictions"], compare=False,
                               asof=asof, probe=False, resolve=resolve,
                               stop_check=stop_check)
        buildable = [r["juris"] for r in pre["rows"]
                     if r.get("status") == "RATED"]
        unbuildable = [r for r in pre["rows"] if r.get("status") != "RATED"]

        rows, summary = pre["rows"], pre["summary"]
        if not offline and buildable:
            if progress:
                progress({"phase": "live", "scenario": i, "of": len(scenarios),
                          "describes": s["describes"],
                          "states": len(buildable)})
            out = sweep.run_config(
                s["config"], buildable, compare=True, asof=asof,
                probe=False, resolve=resolve, stop_check=stop_check,
                progress=(lambda done, total, row:
                          progress({"phase": "live", "scenario": i,
                                    "of": len(scenarios), "done": done,
                                    "total": total, "row": row}))
                if progress else None)
            rows = out["rows"] + unbuildable
            summary = out["summary"]
            # The pre-flight is part of the answer, not a discarded step: a
            # state that could not build never reached ISO, and a run that
            # showed only what it called would report coverage it never had.
            summary["preflight_excluded"] = [
                {"juris": r["juris"], "status": r.get("status"),
                 "detail": r.get("detail", "")} for r in unbuildable]

        summary["layer"] = layer
        summary["basis"] = s["basis"]
        summary["class_code"] = p["class_code"]
        summary["thinning"] = p["thinning"]
        summary["allowance"] = allowance
        line = store.append(summary, rows,
                            label=label or f"{layer} {p['name']}")
        run_ids.append(line["id"])
        results.append({"scenario": s, "summary": summary, "rows": rows,
                        "run_id": line["id"]})
        if scenario_done:
            scenario_done(results[-1])

    p["run_ids"] = run_ids
    p["seconds"] = round(time.time() - started, 1)
    p["rollup"] = rollup(results)
    p["spent_today"] = store.spent_today()
    return {"plan": p, "results": results}


def rollup(results: list) -> dict:
    """One count across every scenario in the run."""
    out = {"scenarios": len(results), "rated": 0, "agree": 0, "differ": 0,
           "premium_only": 0, "not_applicable": 0, "engine_stopped": 0,
           "errors": 0, "live_calls": 0, "undeclared": 0}
    for r in results:
        s = r["summary"]
        out["rated"] += s.get("rated", 0)
        out["agree"] += s.get("agree", 0)
        out["differ"] += len(s.get("differ") or [])
        out["premium_only"] += len(s.get("premium_only") or [])
        out["not_applicable"] += len(s.get("not_applicable") or [])
        out["engine_stopped"] += len(s.get("engine_stopped") or [])
        out["errors"] += len(s.get("errors") or [])
        out["live_calls"] += s.get("live_calls", 0)
    return out


def stored_rollup(limit: int = 500) -> dict:
    """Every stored scenario, summed per layer. What the aggregate card reads.

    **One stored line is one scenario, not one button-press.** A single L3 run
    can append up to twelve lines -- one per configuration -- so this counts
    scenarios, the same unit `rollup()` above counts within a single run.
    Grouped by the label `run()` stamps on each line, `"{layer} {name}"`, the
    same string the Run column already shows -- so a run started from the CLI
    with a custom `--label` is silently excluded rather than mis-bucketed.
    """
    out = {k: {"scenarios": 0, "rated": 0, "agree": 0, "differ": 0,
               "not_applicable": 0, "refused": 0} for k in LAYERS}
    for meta in store.runs(limit=limit):
        layer = _layer_for_label(meta.get("label"))
        if layer is None:
            continue
        s = meta.get("summary") or {}
        o = out[layer]
        o["scenarios"] += 1
        o["rated"] += s.get("rated", 0)
        o["agree"] += s.get("agree", 0)
        o["differ"] += len(s.get("differ") or []) + len(s.get("premium_only") or [])
        o["not_applicable"] += len(s.get("not_applicable") or [])
        o["refused"] += len(s.get("engine_stopped") or []) + len(s.get("errors") or [])
    return out


def _layer_for_label(label) -> str | None:
    label = str(label or "")
    return next((k for k in LAYERS if label == f"{k} {LAYERS[k]['name']}"), None)


def stored_history(limit: int = 500) -> list:
    """Every stored scenario, oldest first. What the aggregate trend reads.

    Same label match as `stored_rollup`, so the trend and the totals above it
    are always counting the same population -- a scenario counted in one and
    not the other would read as a contradiction between two numbers on the
    same page.
    """
    out = []
    for meta in store.runs(limit=limit):
        if _layer_for_label(meta.get("label")) is None:
            continue
        s = meta.get("summary") or {}
        out.append({
            "at_iso": meta.get("at_iso", ""),
            "describes": s.get("describes", ""),
            "compared": bool(s.get("compared")),
            "rated": s.get("rated", 0),
            "agree": s.get("agree", 0),
        })
    out.sort(key=lambda r: r["at_iso"])
    return out


#: Worst-first, for `run_map`. Matches `runstore.qa_rollup`'s rule, applied to
#: one job's in-memory results instead of the stored history -- the Result
#: card needs an answer before the run has ever reached the store.
_MAP_RANK = ("differs", "refused", "uncompared", "partial", "agrees", "untested")


def run_map(results: list) -> dict:
    """Per-jurisdiction status across every scenario in one run, worst-first.

    A jurisdiction that disagreed in even one scenario reads as disagreeing,
    however much else in the same run agreed with it.
    """
    status: dict = {}

    def worse(a, b):
        return a if _MAP_RANK.index(a) <= _MAP_RANK.index(b) else b

    for r in results:
        for row in r.get("rows") or []:
            j, st = row.get("juris"), row.get("status")
            if not j:
                continue
            if st in ("DIFF", "PREMIUM ONLY"):
                here = "differs"
            elif st in ("ENGINE STOPPED", "ENGINE ERROR", "BUILD ERROR", "RAAS FAILED"):
                here = "refused"
            elif st == "MATCH":
                here = "agrees"
            elif st == "RATED":
                here = "uncompared"
            elif st == "NOT APPLICABLE":
                status[j] = worse(status.get(j, "untested"), "partial")
                continue
            else:
                continue
            status[j] = worse(status.get(j, "untested"), here)
    return status


# --------------------------------------------------------------------- the CLI

def _hm(seconds: float) -> str:
    s = int(seconds)
    h, m = divmod(s // 60, 60)
    return f"{h}h {m:02d}m" if h else f"{m} min"


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--layer", choices=sorted(LAYERS))
    ap.add_argument("--class", dest="class_code", default="")
    ap.add_argument("--exposure", default=None)
    ap.add_argument("--juris", action="append", default=[])
    ap.add_argument("--allowance", type=int, default=None,
                    help="live calls this run may spend. States are never cut "
                         "to fit it; the config list is thinned instead")
    ap.add_argument("--size", choices=("full", "reduced"), default="full",
                    help="L3 only: 'full' is the 12-config grid (~612 "
                         "ratings), 'reduced' is the 5-config corners-plus-"
                         "center subset (~255 ratings)")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--plan", action="store_true",
                    help="print what would run, and run nothing")
    ap.add_argument("--layers", action="store_true")
    ap.add_argument("--label", default="")
    a = ap.parse_args(argv)

    if a.layers:
        print("The layered programme\n")
        for k in sorted(LAYERS):
            spec = LAYERS[k]
            print(f"  {k}  {spec['name']}")
            print(f"      {spec['what']}")
            print(f"      varies: {spec['varies']}")
        print(f"\n  Spent today: {store.spent_today()} live calls.")
        return 0

    if not a.layer:
        ap.print_help()
        return 2

    exposure = float(a.exposure) if a.exposure not in (None, "") else None
    try:
        p = plan(a.layer, a.class_code, exposure, a.juris or None,
                 a.allowance, offline=a.offline, size=a.size)
    except PlanError as exc:
        print(f"{exc}")
        return 2

    size_note = f" ({p['size']} grid)" if p["size"] != "full" else ""
    print(f"{a.layer} -- {p['name']}{size_note}")
    print(f"  {p['what']}\n")
    if p["groups"] and p["class_code"]:
        for g in p["groups"]:
            print(f"  basis {g['basis']:<26s} {len(g['jurisdictions'])} "
                  f"jurisdictions")
        if p["undeclared"]:
            print(f"  NOT FILED in {len(p['undeclared'])}: "
                  f"{' '.join(p['undeclared'])}")
    c = p["cost"]
    print(f"\n  scenarios      : {c['scenarios']:,}")
    print(f"  engine ratings : {c['ratings']:,}   "
          f"({_hm(c['offline_seconds'])})")
    print(f"  ISO calls      : {c['live_calls']:,}   "
          f"({_hm(c['live_seconds'])})")
    print(f"  spent today    : {p['spent_today']}")
    t = p["thinning"]
    if t and t.get("applied"):
        print(f"\n  thinned to fit an allowance of {t['allowance']}: "
              f"{t['configs_kept']} of {t['configs_planned']} configs kept, "
              f"all {len(p['jurisdictions'])} jurisdictions kept")
        for d in t["dropped"]:
            print(f"    dropped  {d}")

    if a.plan:
        print("\n  the matrix:")
        for i, s in enumerate(p["scenarios"], 1):
            print(f"    {i:3d}  {s['describes']}")
            print(f"         -> {len(s['jurisdictions'])} jurisdictions"
                  + (f", basis {s['basis']}" if s["basis"] else ""))
        print("\n  nothing was run.")
        return 0

    def progress(ev):
        if ev.get("phase") == "offline":
            print(f"\n  [{ev['scenario']}/{ev['of']}] {ev['describes']}")
            print(f"        offline pre-flight...")
        elif ev.get("phase") == "live" and "states" in ev:
            print(f"        live, {ev['states']} states...")

    out = run(a.layer, a.class_code, exposure, a.juris or None, a.allowance,
              a.offline, progress=progress, label=a.label)
    r = out["plan"]["rollup"]
    print(f"\n  {a.layer} complete in {_hm(out['plan']['seconds'])}")
    print(f"    scenarios run     : {r['scenarios']}")
    print(f"    rated             : {r['rated']}")
    if not a.offline:
        print(f"    agree with ISO    : {r['agree']}")
        print(f"    disagree          : {r['differ'] + r['premium_only']}")
    print(f"    not applicable    : {r['not_applicable']}   "
          f"(a third outcome, never a failure)")
    print(f"    engine refused    : {r['engine_stopped']}")
    print(f"    ISO calls spent   : {r['live_calls']}   "
          f"(today: {out['plan']['spent_today']})")
    if out["plan"]["undeclared"]:
        print(f"    class not filed in: {len(out['plan']['undeclared'])} "
              f"jurisdictions -- a coverage fact, not a failure")
    return 1 if (r["differ"] + r["premium_only"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
