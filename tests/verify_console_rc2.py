#!/usr/bin/env python3
"""The test console's screens, RC-2 (docs/TC-PLAN.md TC-14..TC-19). No ISO calls.

  A  console shell: seven tabs, the call-cap strip, the shared legend (TC-14)

    python tests/verify_console_rc2.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def part_a():
    print("A. console shell (TC-14)")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["RAAS_LEDGER_DIR"] = tmp           # a ledger of our own, so the real one is never read or written
        from console import ledger, status
        from ui import console_page, tester

        code, html, kind = tester.dispatch("GET", "/console", {}, None)
        check("A1 /console is served through the ui mount", code == 200 and kind == "html")
        check("A2 the seven screens, in the brief's order", [label for _, label, _ in console_page.SCREENS] == [
            "Coverage Board", "Readiness Matrix", "Test Plan Builder", "Trace Diff", "Scenario Workbench",
            "Regression Library", "Queue & Run Log"] and html.count('class="tab"') == 7)
        check("A3 no external fonts, scripts or stylesheets (D7)",
              not any(s in html for s in ("<link", "src=\"http", "@import", "fonts.googleapis")))

        c = console_page.cap()
        check("A4 cap strip: 250 in lanes 150 / 50 / 50 (D2)",
              c["cap"] == 250 and [(l["key"], l["cap"]) for l in c["lanes"]] == [("active", 150), ("refresh", 50), ("adhoc", 50)])
        check("A5 empty ledger: 0 used, 250 left, nothing queued", (c["used"], c["left"], c["queued"]) == (0, 250, 0))
        ledger.record(lane="adhoc", origin="test", outcome="rated")
        ledger.record(lane="active", origin="test", outcome="refused", override="test reason")
        c = console_page.cap()
        check("A6 cap strip follows the ledger, per lane and overrides",
              (c["used"], c["left"], c["overrides"]) == (2, 248, 1)
              and {l["key"]: l["used"] for l in c["lanes"]} == {"active": 1, "refresh": 0, "adhoc": 1}, c)
        code, body, kind = tester.dispatch("GET", "/api/console/cap", {}, None)
        check("A7 /api/console/cap returns the same", code == 200 and json.loads(body)["used"] == 2)

        summer = console_page.cap(datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc))
        winter = console_page.cap(datetime(2026, 12, 7, 12, 0, tzinfo=timezone.utc))
        check("A8 resets at 00:00 Eastern, daylight and standard time",
              summer["resets_at"] == "2026-10-08T04:00:00Z" and winter["resets_at"] == "2026-12-08T05:00:00Z",
              (summer["resets_at"], winter["resets_at"]))
        check("A9 the legend is TC-08's vocabulary, every state",
              [g["key"] for g in console_page.legend()] == [s.key for s in status.ALL]
              and all(f'chip.{s.key}' in html for s in status.ALL))
        check("A10 the shell spends no call: no POST route", console_page.dispatch("POST", "/console", {}, {}) is None)
        os.environ.pop("RAAS_LEDGER_DIR")


def main() -> int:
    part_a()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
