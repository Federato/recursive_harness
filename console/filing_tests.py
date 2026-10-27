"""Test a carrier filing from the Carrier Filings screen: quick checks on our engine, and an optional ISO spot check.

Not the full proof (the suites behind the Deviations Proof board); a check anyone can run in a minute:

  * **The filed factors apply as written.** Typical businesses (`deviations.impact`'s set) are priced twice, technical
    (pure ISO) and carrier, and each coverage's carrier premium is compared with technical x the filed factor for that
    class and coverage, row by row of the filing. A row passes when its total is within `FACTOR_TOL` of the factor (1% GL, 2.5% Property);
    single risks stray further on small premiums because ISO rounds the rate, so their range is shown, not judged.
    Policy items (a minimum premium) are checked on every risk; parts the typical set never reaches are listed.
  * **The effect is what we expect.** The same risks against the impact recorded when the filing went into use
    (`results/impact`), risk for risk, scaled onto the recorded effect for the whole typical set: the estimate is the
    recorded effect when nothing changed. Expected defaults to the recorded effect; a figure typed on the screen
    (`expected.json`) replaces it. Within `EFFECT_TOL` points passes.
  * **ISO agrees** (optional, spends calls). D21: ISO only ever rates TECHNICAL, never a company's factors. One sampled
    risk per state is sent as its technical request, and ISO's premium must equal our technical; with the first
    check, carrier = ISO x the filed factors. A request ISO has already answered is free.

Quick (default) prices one risk per class (medium size; one construction for Property); full prices the whole set.
One test runs at a time (the low-memory rule); "every filing" queues them. Results: results/deviations/filing_tests/.
"""
from __future__ import annotations

import json
import threading
import time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
#: a filed row's total within this of its factor. Property is looser: a coverage's premium carries parts ISO prices at
#: another group's factor or none (the engine applies factors part by part; T5 proved that against ISO), so a whole
#: coverage only approximates its factor. Both still tell a wrong class group, company or a missing factor (6%+ apart).
FACTOR_TOL = {"GL": Decimal("0.01"), "CF": Decimal("0.025")}
EFFECT_TOL = 1.0                      # points either side of the expected effect
QUICK_SIZE, QUICK_CONSTRUCTION = "Medium", "Joisted masonry"
COVERAGE = {"Group I": ("GroupI", "Fire and lightning"), "Group II": ("GroupII", "Wind and hail"),
            "Special": ("Special", "Special form"), "Broad": ("Broad", "Broad form"),
            "Earthquake": ("Earthquake", "Earthquake"),
            "Premises/Operations": ("PremOps", "Premises and operations"),
            "Products/Completed Ops": ("ProdsCompldOps", "Products and completed work")}
STATE = {"queue": [], "job": None, "lock": threading.Lock()}


def _dir() -> Path:
    import os
    d = Path(os.environ.get("FILING_TESTS_DIR") or ROOT / "results" / "deviations" / "filing_tests")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write(p: Path, data) -> None:
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(p)


def result(serff: str) -> dict | None:
    return _read(_dir() / f"{serff}.json", None)


def expected_overrides() -> dict:
    return _read(_dir() / "expected.json", {})


def set_expected(serff: str, company: str, state: str, value) -> dict:
    """A typed expected effect (percent vs ISO) for one company in one state; None clears it."""
    d = expected_overrides()
    key = f"{company}|{state}"
    if value in (None, ""):
        d.get(serff, {}).pop(key, None)
    else:
        d.setdefault(serff, {})[key] = float(value)
    _write(_dir() / "expected.json", d)
    return d.get(serff, {})


# ------------------------------------------------------------------ the filing

def _filing(serff: str) -> dict:
    from console import filings
    f = next((x for x in filings.filings()["filings"] if x["serff"] == serff), None)
    if f is None:
        raise KeyError(f"no filing {serff}")
    return f


def _states(f: dict) -> list:
    return [s.strip() for s in str(f.get("state", "")).split(",") if s.strip()]


def _companies(f: dict) -> list:
    """The companies with a version of this filing in use."""
    return list(dict.fromkeys(v["company"] for v in f.get("versions", []) if v.get("status") == "approved"))


def _recorded(f: dict, company: str, state: str) -> dict | None:
    """The impact file recorded for this company, line and state: its effect there and its risks."""
    from console.filings import _impact_dir, _json
    for i in f.get("impacts", []):
        if i["company"] != company or i.get("draft") or state not in (i.get("states") or {}):
            continue
        d = _json(_impact_dir() / i["file"])
        return {"file": i["file"], "generated": d.get("generated"),
                "effect": float((d.get("by_state", {}).get(state) or d.get("all") or {}).get("change") or 0),
                "risks": [r for r in d.get("risks", []) if r["state"] == state]}
    return None


def _sample(line: str, state: str, full: bool):
    from deviations import impact as I
    for risk, cfg in I._risks(line, state):
        if full or (risk.size == QUICK_SIZE and (line != "CF" or risk.construction == QUICK_CONSTRUCTION)):
            yield risk, cfg


def _key(r: dict) -> tuple:
    return (r["state"], r["risk_type"], r["class"], r["size"], r.get("construction") or "")


def _class_label(plan, cls: str) -> str:
    groups = (plan.manifest or {}).get("class_groups") or {}
    grp = next((g for g, codes in groups.items() if cls in codes), None)
    if not grp:
        return "all other classes"
    tail = grp.split("@")[0].rsplit("-", 1)[-1]
    return f"class group {tail}"


def _filed(plan, line: str, cls: str, cov_key: str, iso_lcm: Decimal):
    """The filed factor for one class and coverage, as carrier / technical: (ratio, the row it comes from) or None."""
    if line == "CF":
        entry = plan.group_lcm.get((cov_key, "Class", cls)) or plan.unlisted_lcm.get((cov_key, "Class"))
    else:
        entry = plan.lcm.get((cov_key, cls)) or plan.unlisted_lcm.get((cov_key,))
    if entry is None:
        return None
    value, mode, cite = entry
    return (value / iso_lcm if mode == "replace" and iso_lcm else value), cite


# ------------------------------------------------------------------ the run

def run(serff: str, full: bool = False, progress=None) -> dict:
    from deviations import impact as I
    from deviations.engine import book_for, iso_state_lcm, plan_for
    f = _filing(serff)
    line, states, companies = f["line"], _states(f), _companies(f)
    total = sum(1 for st in states for _ in _sample(line, st, full)) * len(companies)
    done, started = 0, time.strftime("%Y-%m-%dT%H:%M:%S")
    rows: dict = {}
    policy: dict = {}
    effects, risks_out, unreached = [], [], set()
    overrides = expected_overrides().get(serff, {})
    for co in companies:
        for st in states:
            date = I._filing_date(co, line, st, I.CARRIERS_ROOT)
            plan = plan_for(line, co, st, date, "New")
            iso_lcm = iso_state_lcm(book_for(plan), line)
            rated = []
            for risk, cfg in _sample(line, st, full):
                r = I._rate_one(line, co, st, date, risk, cfg, I.CARRIERS_ROOT, plan)
                done += 1
                if progress:
                    progress(done, total)
                if r.status != "rated":
                    continue
                rated.append(r)
                label = _class_label(plan, r.class_code)
                for g, (t, c) in r.by_group.items():
                    if g not in COVERAGE or not t:
                        continue
                    key, name = COVERAGE[g]
                    got = _filed(plan, line, r.class_code, key, iso_lcm)
                    ratio, cite = got if got else (Decimal(1), "not in the filing: ISO's rate")
                    k = (co, st, name, label if got else "classes the filing leaves at ISO's rate", str(ratio))
                    row = rows.setdefault(k, {"company": co, "state": st, "coverage": name, "appliesTo": k[3],
                                              "filed": ratio, "cite": cite, "risks": 0, "t": Decimal(0), "c": Decimal(0),
                                              "lo": None, "hi": None})
                    row["risks"] += 1
                    row["t"] += t
                    row["c"] += c
                    each = c / t
                    row["lo"] = each if row["lo"] is None else min(row["lo"], each)
                    row["hi"] = each if row["hi"] is None else max(row["hi"], each)
            # policy items the typical risks reach: the minimum premium
            for item, (value, mode, cite) in plan.policy.items():
                if item == "MIN:Policy":
                    raised = [r for r in rated if r.carrier == value and r.technical < value]
                    under = [r for r in rated if r.carrier < value]
                    policy[(co, st, item)] = {"company": co, "state": st, "item": "Minimum premium",
                                              "filed": f"${value.normalize():,f}", "risks": len(rated),
                                              "raised": len(raised), "under": len(under), "ok": not under,
                                              "got": (f"none under ${value.normalize():,f}; {len(raised)} raised to it"
                                                      if not under else f"{len(under)} priced under it")}
                else:
                    unreached.add({"PCT:Terrorism": "Terrorism charge (no typical business takes terrorism cover)"}
                                  .get(item, item))
            for t in plan.overrides:
                unreached.add({"ExpectedLossRatio": "Experience rating expected loss ratio (needs an experience-rated "
                                                    "risk; the proving suite checks it)"}.get(t, t))
            # the effect: the same risks against what was recorded, scaled onto the recorded whole-set effect
            rec = _recorded(f, co, st)
            now_t = sum((r.technical for r in rated), Decimal(0))
            now_c = sum((r.carrier for r in rated), Decimal(0))
            eff = {"company": co, "state": st, "risks": len(rated), "full": full}
            if rec:
                base = {_key(x): x for x in rec["risks"] if x["status"] == "rated"}
                pairs = [(r, base.get((r.state, r.risk_type, r.class_code, r.size, r.construction or ""))) for r in rated]
                pairs = [(r, b) for r, b in pairs if b]
                bt = sum((Decimal(b["technical"]) for _, b in pairs), Decimal(0))
                bc = sum((Decimal(b["carrier"]) for _, b in pairs), Decimal(0))
                pt = sum((r.technical for r, _ in pairs), Decimal(0))
                pc = sum((r.carrier for r, _ in pairs), Decimal(0))
                if bt and bc and pt and not full:
                    now = ((1 + rec["effect"] / 100) * float((pc / bc) / (pt / bt)) - 1) * 100
                    eff["basis"] = "scaled"
                else:                  # the whole set, or a recorded impact without its risks: the sample's own effect
                    now = float((now_c / now_t - 1) * 100) if now_t else None
                    eff["basis"] = "full" if full else "sample"
                moved = [{"class": r.class_code, "riskType": r.risk_type, "size": r.size,
                          "construction": r.construction, "was": b["carrier"], "now": str(r.carrier)}
                         for r, b in pairs if Decimal(b["carrier"]) != r.carrier][:20]
                eff.update(recorded=rec["effect"], recordedAt=rec["generated"], matched=len(pairs), moved=moved,
                           movedCount=sum(1 for r, b in pairs if Decimal(b["carrier"]) != r.carrier))
            else:
                now = float((now_c / now_t - 1) * 100) if now_t else None
                eff.update(recorded=None, matched=0, moved=[], movedCount=0, basis="full" if full else "sample")
            exp = overrides.get(f"{co}|{st}", eff.get("recorded"))
            eff.update(now=round(now, 1) if now is not None else None, expected=exp,
                       expectedFrom="yours" if f"{co}|{st}" in overrides else ("recorded" if exp is not None else None))
            eff["ok"] = None if exp is None or now is None else abs(now - exp) <= EFFECT_TOL
            effects.append(eff)
            risks_out += [{"company": co, "state": st, "riskType": r.risk_type, "class": r.class_code, "size": r.size,
                           "construction": r.construction, "technical": str(r.technical), "carrier": str(r.carrier),
                           "driver": r.driver} for r in rated]
    factors = []
    for row in rows.values():
        got = row["c"] / row["t"] if row["t"] else None
        ok = got is not None and abs(got / row["filed"] - 1) <= FACTOR_TOL[line]
        factors.append({k: row[k] for k in ("company", "state", "coverage", "appliesTo", "risks", "cite")}
                       | {"filed": _pct(row["filed"]), "got": _pct(got), "lo": _pct(row["lo"]), "hi": _pct(row["hi"]),
                          "ok": ok})
    factors.sort(key=lambda x: (x["company"], x["state"], x["appliesTo"] != "all other classes", x["appliesTo"], x["coverage"]))
    pol = list(policy.values())
    out = {"serff": serff, "id": f.get("id"), "line": line, "states": states, "companies": companies,
           "mode": "full" if full else "quick", "started": started, "ranAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "priced": done, "factors": factors, "policy": pol, "unreached": sorted(unreached), "effects": effects,
           "risks": risks_out, "tolerance": {"factor": float(FACTOR_TOL[line] * 100), "effect": EFFECT_TOL},
           "iso": (result(serff) or {}).get("iso")}
    out["ok"] = {"factors": all(x["ok"] for x in factors) and all(p["ok"] for p in pol) if factors or pol else None,
                 "effect": (all(e["ok"] for e in effects if e["ok"] is not None)
                            if any(e["ok"] is not None for e in effects) else None)}
    _write(_dir() / f"{serff}.json", out)
    return out


def _pct(x) -> float | None:
    return None if x is None else float(((Decimal(x) - 1) * 100).quantize(Decimal("0.1")))


def rejudge(serff: str) -> dict | None:
    """After an expected figure is typed: the effect check judged again from the stored run, no pricing."""
    out = result(serff)
    if not out:
        return None
    ov = expected_overrides().get(serff, {})
    for e in out["effects"]:
        k = f"{e['company']}|{e['state']}"
        e["expected"] = ov.get(k, e.get("recorded"))
        e["expectedFrom"] = "yours" if k in ov else ("recorded" if e["expected"] is not None else None)
        e["ok"] = None if e["expected"] is None or e["now"] is None else abs(e["now"] - e["expected"]) <= EFFECT_TOL
    out["ok"]["effect"] = (all(e["ok"] for e in out["effects"] if e["ok"] is not None)
                           if any(e["ok"] is not None for e in out["effects"]) else None)
    _write(_dir() / f"{serff}.json", out)
    return out


# ------------------------------------------------------------------ the queue (one at a time)

def start(serffs: list, full: bool = False) -> dict:
    with STATE["lock"]:
        busy = {j["serff"] for j in STATE["queue"]} | ({STATE["job"]["serff"]} if STATE["job"] else set())
        for s in serffs:
            if s not in busy:
                STATE["queue"].append({"serff": s, "full": bool(full), "state": "waiting", "done": 0, "total": 0})
        if STATE["job"] is None and STATE["queue"]:
            threading.Thread(target=_worker, daemon=True).start()
            STATE["job"] = {"serff": STATE["queue"][0]["serff"], "state": "starting", "done": 0, "total": 0}
    return status()


def _worker() -> None:
    while True:
        with STATE["lock"]:
            if not STATE["queue"]:
                STATE["job"] = None
                return
            job = STATE["queue"].pop(0)
            job["state"] = "running"
            STATE["job"] = job

        def tick(d, t, job=job):
            job["done"], job["total"] = d, t
        try:
            run(job["serff"], job["full"], progress=tick)
        except Exception as exc:                               # noqa: BLE001 (shown on the screen)
            prev = result(job["serff"]) or {}
            prev["error"] = f"{type(exc).__name__}: {exc}"[:300]
            prev["serff"] = job["serff"]
            _write(_dir() / f"{job['serff']}.json", prev)


def status() -> dict:
    with STATE["lock"]:
        return {"running": dict(STATE["job"]) if STATE["job"] else None,
                "waiting": [j["serff"] for j in STATE["queue"]]}


def summaries() -> dict:
    """Each filing's last test, short: what the cards and the summary strip show."""
    out = {}
    for p in _dir().glob("*.json"):
        if p.name == "expected.json":
            continue
        d = _read(p, {})
        if d.get("serff"):
            out[d["serff"]] = {"ranAt": d.get("ranAt"), "mode": d.get("mode"), "ok": d.get("ok"),
                               "error": d.get("error"), "iso": (d.get("iso") or {}).get("ok")}
    return out


# ------------------------------------------------------------------ the ISO spot check (technical only, D21)

def _spot_requests(serff: str) -> list:
    """One sampled risk per state, as the TECHNICAL request ISO would be sent; one ISO has answered first, if any."""
    from console import workbench as WB
    from deviations import impact as I
    from deviations.engine import iso_request
    f = _filing(serff)
    line, co = f["line"], (_companies(f) or [None])[0]
    out = []
    for st in _states(f):
        date = I._filing_date(co, line, st, I.CARRIERS_ROOT)
        best = None
        for risk, cfg in _sample(line, st, False):
            req = _request(line, st, date, cfg)
            req["header"].update(WritingCompany=co, PolicyType="New")
            plain, _ = iso_request(req, line)
            have = WB.stored(plain)
            cand = {"state": st, "class": risk.class_code, "riskType": risk.risk_type, "size": risk.size,
                    "construction": risk.construction, "request": plain, "stored": have}
            if best is None:
                best = cand
            if have and have.get("outcome") == "rated":
                best = cand
                break
        if best:
            out.append(best)
    return out


def _request(line: str, state: str, date: str, cfg: dict) -> dict:
    """The typical risk's request, built the way `deviations.impact` builds it."""
    from console import catalog
    if line == "CF":
        return catalog.build("CP", state, {**cfg, "effective_date": date})
    import variants as V
    d = V.Declared(state, date.replace("-", ""))
    basis = d.basis_for(cfg["class_code"], "PremOps")
    exposure = int(Decimal(catalog.basis_exposure(basis)) * cfg["_size"]) or 1
    return catalog.build("GL", state, {"class_code": cfg["class_code"], "exposure": exposure,
                                       "effective_date": date.replace("-", "")})


def _spot_view(reqs: list) -> list:
    return [{k: v for k, v in r.items() if k != "request"} for r in reqs]


def iso_plan(serff: str) -> dict:
    reqs = _spot_requests(serff)
    calls = sum(1 for r in reqs if not (r["stored"] and r["stored"].get("outcome") == "rated"))
    return {"serff": serff, "requests": _spot_view(reqs), "calls": calls, "last": (result(serff) or {}).get("iso")}


def iso_send(serff: str, override: str | None = None, client=None) -> dict:
    """Ask ISO (or reuse its stored answer) and compare its premium with our technical, request by request."""
    from console import workbench as WB
    f = _filing(serff)
    wl = "CP" if f["line"] == "CF" else "GL"
    rows, sent = [], 0
    for r in _spot_requests(serff):
        got = WB.send(wl, r["request"], reuse=True, override=override, client=client)
        sent += 1 if got.get("sent") else 0
        if got.get("error"):
            rows.append({**_spot_view([r])[0], "ok": None, "detail": got["error"], "capped": got.get("capped")})
            continue
        ours = WB.rate(wl, r["request"])
        st = got.get("stored") or {}
        iso = st.get("iso")
        ok = None if iso in (None, "None") or ours.get("outcome") != "rated" else \
            Decimal(str(iso)) == Decimal(str(ours["premium"]))
        rows.append({**_spot_view([r])[0], "ours": ours.get("premium"), "iso": iso, "ok": ok,
                     "scenario": st.get("scenario"), "reused": bool(got.get("reused"))})
    rep = {"ranAt": time.strftime("%Y-%m-%dT%H:%M:%S"), "sent": sent, "rows": rows,
           "ok": all(x["ok"] for x in rows) if rows and all(x["ok"] is not None for x in rows) else None}
    prev = result(serff) or {"serff": serff}
    prev["iso"] = rep
    _write(_dir() / f"{serff}.json", prev)
    return rep
