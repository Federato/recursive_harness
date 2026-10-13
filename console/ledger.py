"""Every RaaS call, wherever it starts, against the daily cap and its lanes (TC-12; the user's D2 and D21).

**Cap 250 calls a day, in three lanes:** `active` 150 (committed console plans), `refresh` 50 (stale references and
changed content), `adhoc` 50 (everything else: the rate page `/`, command-line tools, the chunk scripts). A call is
counted when it is sent, whatever comes back (TC-03: refusals and errors included). The day resets at 00:00 Eastern.

`scripts/raas.py` calls `admit()` before every call and `record()` after it, so nothing reaches ISO uncounted. A full
lane stops the call unless an **override** is given, with a reason (`RaaS(override="...")` or the environment variable
`RAAS_OVERRIDE`); the override and its reason are in the log.

The log is `results/tc/ledger-YYYY-MM.jsonl` (one line per call), or `RAAS_LEDGER_DIR` (tests).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAP = 250
LANES = {"active": 150, "refresh": 50, "adhoc": 50}


class CapReached(RuntimeError):
    pass


def _dir() -> Path:
    return Path(os.environ.get("RAAS_LEDGER_DIR") or (ROOT / "results" / "tc"))


def _et(now: datetime | None = None) -> datetime:
    """Eastern time without a tz database: US daylight time from the 2nd Sunday of March to the 1st Sunday of
    November, at 02:00 local."""
    utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    y = utc.year

    def nth_sunday(month: int, n: int) -> datetime:
        d = datetime(y, month, 1, tzinfo=timezone.utc)
        d += timedelta(days=(6 - d.weekday()) % 7)
        return d + timedelta(weeks=n - 1)

    start = nth_sunday(3, 2) + timedelta(hours=7)       # 02:00 EST = 07:00 UTC
    end = nth_sunday(11, 1) + timedelta(hours=6)        # 02:00 EDT = 06:00 UTC
    return utc + timedelta(hours=-4 if start <= utc < end else -5)


def day(now: datetime | None = None) -> str:
    return _et(now).strftime("%Y-%m-%d")


def _file(d: str) -> Path:
    return _dir() / f"ledger-{d[:7]}.jsonl"


def entries(d: str | None = None) -> list:
    d = d or day()
    f = _file(d)
    if not f.exists():
        return []
    out = []
    for raw in f.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(raw)
        except ValueError:
            continue
        if e.get("day") == d:
            out.append(e)
    return out


def used(d: str | None = None) -> dict:
    """Calls counted today, per lane and in total."""
    out = {lane: 0 for lane in LANES}
    for e in entries(d):
        out[e.get("lane", "adhoc")] = out.get(e.get("lane", "adhoc"), 0) + 1
    out["total"] = sum(out[lane] for lane in LANES)
    return out


def origin_default() -> str:
    return Path(sys.argv[0]).name if sys.argv and sys.argv[0] else "python"


def admit(lane: str = "adhoc", override: str | None = None) -> str | None:
    """Raise CapReached when this lane (or the day) is full and no override reason is given. Returns the override used."""
    if lane not in LANES:
        raise ValueError(f"unknown lane {lane!r}; one of {sorted(LANES)}")
    override = override or os.environ.get("RAAS_OVERRIDE") or None
    u = used()
    if u[lane] < LANES[lane] and u["total"] < CAP:
        return None
    if override:
        return override
    raise CapReached(f"the {lane} lane is full today ({u[lane]} of {LANES[lane]}; {u['total']} of {CAP} in all). "
                     f"Give a reason to override: RaaS(override='...') or RAAS_OVERRIDE='...'")


def record(*, lane: str, origin: str, outcome: str, status: int | None = None, line: str = "", state: str = "",
           request_hash: str = "", override: str | None = None, answer: str = "") -> dict:
    e = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "day": day(), "lane": lane,
         "origin": origin, "outcome": outcome, "status": status, "line": line, "state": state,
         "hash": request_hash, "answer": answer}
    if override:
        e["override"] = override
    f = _file(e["day"])
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(e) + "\n")
    return e
