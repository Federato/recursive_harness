"""One index over every ISO answer we hold (TC-06), and which of them are stale (TC-07).

Nothing on disk moves: the index points at the files where each answer already lives.

  * `results/cf-raas/<name>_request.json` with `_response.json` (ISO rated) or `_refusal.json` (ISO refused)
  * `results/failed-calls/<stamp>-<state>-<status>/request.json` + `response.txt` (refusals the client captured)
  * `results/tc/answers/<hash>_{request,response,refusal}.json` (every answer the ledger saves from now on, D21)
  * the GL run store (`results/runs-*.jsonl`): **premium-level only**, our premium and ISO's per state, no bodies

**One entry per distinct request** (`hash`: sha256 of the request body, keys sorted, the auth header left out), so a
request sent twice is one reference; its latest answer stands and every file is listed.

**Stale** (TC-07): the answer was given on an ISO package other than the one our corpus now resolves for its state and
date -- ISO's content changed underneath it, or ours did (a corpus refresh, C28-20). Premium-level GL rows carry our
package only, so their staleness is "unknown" until a full answer replaces them.

    from console import store
    idx = store.build()          # scans and writes results/tc/reference_index.json
    idx = store.load()           # the last build
"""
from __future__ import annotations

import glob
import hashlib
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
INDEX = RES / "tc" / "reference_index.json"
ANSWERS = RES / "tc" / "answers"

PKG = re.compile(r"\b(CF|GL) ([A-Z]{2}) (\d{8}) (V\d\d)\b")
SCHEME = re.compile(r'"Scheme"\s*:\s*"([^"]+)"')


def request_hash(payload: dict) -> str:
    body = payload.get("body", payload) if isinstance(payload, dict) else payload
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:24]


def _keys(payload: dict) -> tuple[str, str, str]:
    body = payload.get("body", payload)
    sk = body.get("SchemeKeys") or {}
    name = sk.get("ProductName") or ""
    line = "CP" if name.startswith("Commercial Property") else "GL" if name.startswith("General Liability") else "?"
    return line, (name.split() or ["?"])[-1], (sk.get("EffectiveDateTime") or "")[:10]


def _state_pkg(text: str, line: str) -> str | None:
    """The state package named in an ISO answer (its Scheme, or a refusal's Project), never countrywide's."""
    m = SCHEME.search(text)
    cands = PKG.findall(m.group(1) if m else text)
    for fam, st, ed, v in cands:
        if st != "CW":
            return f"{fam}_{st}_{ed}_{v}"
    return None


def _mtime(p: Path) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(p.stat().st_mtime))


def _add(entries: dict, payload: dict, outcome: str, answer: Path, request: Path, note: str = "") -> None:
    try:
        h = request_hash(payload)
        line, state, date = _keys(payload)
        text = answer.read_text(encoding="utf-8", errors="replace")
    except Exception:                                         # noqa: BLE001 -- an unreadable file is skipped
        return
    at = _mtime(answer)
    e = entries.get(h)
    files = [request.relative_to(ROOT).as_posix(), answer.relative_to(ROOT).as_posix()]   # portable: the Mac package reads it
    if e is None or at >= e["stored_at"]:
        msg = ""
        if outcome == "refused":
            m = re.search(r'"(?:Message|message)"\s*:\s*"([^"]{0,300})', text)
            msg = m.group(1) if m else text[:300]
        new = {"hash": h, "line": line, "state": state, "date": date, "outcome": outcome,
               "iso_package": _state_pkg(text, line), "message": msg, "stored_at": at,
               "files": sorted(set(files + (e["files"] if e else []))), "sends": (e["sends"] + 1) if e else 1}
        if note:
            new["note"] = note
        entries[h] = new
    else:
        e["files"] = sorted(set(e["files"] + files))
        e["sends"] += 1


def _scan(entries: dict) -> None:
    for f in sorted(glob.glob(str(RES / "cf-raas" / "*_request.json"))) + \
            sorted(glob.glob(str(ANSWERS / "*_request.json"))):
        req = Path(f)
        base = f[:-len("_request.json")]
        for suffix, outcome in (("_response.json", "rated"), ("_refusal.json", "refused")):
            ans = Path(base + suffix)
            if ans.exists():
                try:
                    payload = json.loads(req.read_text(encoding="utf-8"))
                except Exception:                             # noqa: BLE001
                    continue
                _add(entries, payload, outcome, ans, req)
    _scan_response_only(entries)
    for d in sorted((RES / "failed-calls").glob("*")):
        req, ans = d / "request.json", d / "response.txt"
        if req.exists() and ans.exists():
            try:
                payload = json.loads(req.read_text(encoding="utf-8"))
            except Exception:                                 # noqa: BLE001
                continue
            _add(entries, payload, "refused", ans, req, note="captured by the RaaS client")


def _scan_response_only(entries: dict) -> None:
    """ISO answers kept without their request (637 on 2026-10-06).

    Chunk 13's 293 ISO fixtures: the request is rebuilt exactly from ISO's own STC file, as `157_` sends it (the
    fixture's `CommercialProperty` at 2026-09-17), so they get a real request hash. The rest (chunks 13 and 14 state
    sweeps, a few probes) are indexed by the state, date and package their response names, flagged `request_kept:
    false`: only their chunk script can rebuild the request.
    """
    stc = None
    for f in sorted(glob.glob(str(RES / "cf-raas" / "*_response.json"))):
        base = f[:-len("_response.json")]
        if Path(base + "_request.json").exists():
            continue
        ans = Path(f)
        name = ans.name[:-len("_response.json")]
        if name.startswith("chunk13_fixture_"):
            if stc is None:
                from cf_engine.config import CORPUS_ROOT
                stc = {p.stem: p for p in Path(CORPUS_ROOT).rglob("STC/*.json")}
            fx = stc.get(name[len("chunk13_fixture_"):])
            if fx is not None:
                d = json.loads(fx.read_text(encoding="utf-8-sig"))
                payload = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                                 "EffectiveDateTime": "2026-09-17T00:00:00"},
                                                  "CommercialProperty": d["CommercialProperty"]}}
                _add(entries, payload, "rated", ans, fx if fx.is_relative_to(ROOT) else ans,
                     note=f"request rebuilt from ISO's fixture {fx.name} (as 157_ sends it)")
                continue
        try:
            text = ans.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        pkg = _state_pkg(text, "")
        m = re.search(r'"EffectiveDt"\s*:\s*"(\d{4}-\d{2}-\d{2})', text)
        if not pkg:
            continue
        fam, st = pkg.split("_")[0], pkg.split("_")[1]
        h = "resp-" + hashlib.sha256(name.encode()).hexdigest()[:19]
        entries[h] = {"hash": h, "line": "CP" if fam == "CF" else "GL", "state": st, "date": m.group(1) if m else "",
                      "outcome": "rated", "iso_package": pkg, "message": "", "stored_at": _mtime(ans),
                      "files": [ans.relative_to(ROOT).as_posix()], "sends": 1, "request_kept": False,
                      "note": "request not kept: rebuilt by its chunk script"}


def _gl_runs() -> list:
    """Premium-level GL references from the run store: compared rows with ISO's premium."""
    out = []
    for f in sorted(glob.glob(str(RES / "runs-*.jsonl"))):
        for raw in Path(f).read_text(encoding="utf-8").splitlines():
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            s = line.get("summary") or {}
            if not s.get("compared"):
                continue
            for r in line.get("rows") or []:
                if r.get("iso") in (None, ""):
                    continue
                # a run that varies the effective date records it per row (sweep's `asof`); the run's is the default
                out.append({"kind": "premium-only", "line": "GL", "state": r.get("juris"), "date": r.get("asof") or s.get("asof", ""),
                            "hash": f"gl:{line.get('id')}:{r.get('juris')}", "iso_package": r.get("iso_package") or "",
                            "fingerprint": s.get("fingerprint", ""), "describes": s.get("describes", ""),
                            "ours": r.get("ours"), "iso": r.get("iso"), "status": r.get("status"),
                            "our_packages": r.get("packages", ""), "run": line.get("id"), "at": line.get("at_iso")})
    return out


_CURRENT: dict = {}


def current_package(line: str, state: str, date: str) -> str | None:
    """The state package our corpus resolves now for (state, date)."""
    key = (line, state, date)
    if key not in _CURRENT:
        asof = date.replace("-", "")
        try:
            if line == "CP":
                from cf_engine.resolve import book_for
                _CURRENT[key] = book_for(state, asof).resolution.state.pkg_id
            elif line == "GL":
                from gl_engine.resolve import EditionResolver
                _CURRENT[key] = EditionResolver().resolve(state, asof).state.pkg_id
            else:
                _CURRENT[key] = None
        except Exception:                                     # noqa: BLE001 -- no package for that state / date
            _CURRENT[key] = None
    return _CURRENT[key]


def staleness(e: dict) -> tuple[str, str]:
    """('fresh' | 'stale' | 'unknown', why)."""
    if e.get("kind") == "premium-only" and not e.get("iso_package"):
        return "unknown", "premium-level row: no ISO package recorded"
    iso = e.get("iso_package")
    if not iso:
        return "unknown", "ISO's answer names no state package"
    now = current_package(e["line"], e["state"], e["date"])
    if now is None:
        return "unknown", "no package resolves now for this state and date"
    if now != iso:
        return "stale", f"answered on {iso}; {now} is in force for this date now"
    return "fresh", ""


def build() -> dict:
    import sys
    sys.path.insert(0, str(ROOT))
    entries: dict = {}
    _scan(entries)
    refs = sorted(entries.values(), key=lambda e: (e["line"], e["state"], e["date"], e["hash"]))
    for e in refs:
        e["freshness"], e["stale_reason"] = staleness(e)
    gl = _gl_runs()
    for e in gl:
        e["freshness"], e["stale_reason"] = staleness(e)
    idx = {"built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "references": refs, "gl_premium_rows": gl}
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(idx, indent=0), encoding="utf-8")
    return idx


def load() -> dict:
    """The last build. File paths are relative to the harness and read with forward slashes, whichever system wrote
    them, so one index serves Windows and the Mac package alike."""
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    for e in idx.get("references", []):
        e["files"] = [f.replace("\\", "/") for f in e.get("files", [])]
    return idx


def freshness(idx: dict | None = None) -> dict:
    """reference hash -> 'fresh' | 'stale' | 'unknown', over full answers and GL's premium-level rows alike."""
    try:
        idx = idx or load()
    except FileNotFoundError:
        return {}
    return {e["hash"]: e.get("freshness", "unknown")
            for e in idx.get("references", []) + idx.get("gl_premium_rows", []) if e.get("hash")}


def lookup(payload: dict, idx: dict | None = None) -> dict | None:
    """The stored answer for exactly this request, if any (the dedupe check before a call)."""
    h = request_hash(payload)
    newer = answer_entry(h, payload)
    for e in (idx or load())["references"]:
        if e["hash"] == h:
            # a refresh (or any re-send) since the index was built: the ledger's newer answer is the one in force
            if newer and newer["stored_at"] > e["stored_at"]:
                return {**newer, "files": sorted(set(e["files"]) | set(newer["files"]), key=lambda f: f == newer["files"][-1]),
                        "sends": e.get("sends", 1) + 1}
            return e
    return newer


def answer_entry(h: str, payload: dict) -> dict | None:
    """An answer the ledger kept since the index was last built (`results/tc/answers/<hash>_*.json`), as an index
    entry, so a call made a minute ago is found by the next dedupe without waiting for `build()`."""
    resp, ref, req = ANSWERS / f"{h}_response.json", ANSWERS / f"{h}_refusal.json", ANSWERS / f"{h}_request.json"
    ans = resp if resp.exists() else ref if ref.exists() else None
    if ans is None:
        return None
    try:
        line, state, date = _keys(payload)
    except Exception:                                         # noqa: BLE001
        line, state, date = "", "", ""
    msg = ""
    if ans is ref:
        try:
            msg = json.loads(ref.read_text(encoding="utf-8")).get("message", "")[:300]
        except ValueError:
            pass
    text = ans.read_text(encoding="utf-8", errors="replace")
    return {"hash": h, "line": line, "state": state, "date": date, "outcome": "rated" if ans is resp else "refused",
            "iso_package": _state_pkg(text, line), "message": msg, "stored_at": _mtime(ans),
            "files": [p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p) for p in (req, ans) if p.exists()],
            "sends": 1,
            "freshness": "fresh", "stale_reason": "", "note": "kept by the ledger since the index was built"}


def save_answer(payload: dict, response: dict | None, refusal: str | None) -> Path:
    """Keep one answer from the ledger (D21): request plus response or refusal, named by request hash."""
    ANSWERS.mkdir(parents=True, exist_ok=True)
    h = request_hash(payload)
    (ANSWERS / f"{h}_request.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    if response is not None:
        p = ANSWERS / f"{h}_response.json"
        p.write_text(json.dumps(response, indent=1), encoding="utf-8")
    else:
        p = ANSWERS / f"{h}_refusal.json"
        p.write_text(json.dumps({"message": refusal or ""}, indent=1), encoding="utf-8")
    return p
