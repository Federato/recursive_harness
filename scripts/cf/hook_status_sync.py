#!/usr/bin/env python3
"""Stop hook: are the Property status docs (and the deployed status page) still in sync? (user, 2026-10-01)

Runs check_status_docs.check() each time Claude finishes a turn. When something disagrees it exits 2 with the
problems on stderr, so Claude is told and fixes them before stopping (task list -> CF-BUILD-STATUS.html -> START-HERE,
then scripts/cf/sync_status_page.py --push for the deployed copy). When stop_hook_active is set (Claude is already
continuing because of this hook) it exits 0, so it can never loop. Offline / no Ideation checkout: the deployed
comparison is skipped, the local docs are still checked.

The premium census (check_premium_census.py, ~55 s) is too slow for every turn; it runs at gates via 104_.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    if payload.get("stop_hook_active"):
        return 0
    import check_status_docs
    with contextlib.redirect_stdout(io.StringIO()):
        problems = check_status_docs.check(deployed=True)
    if not problems:
        return 0
    print("Property status docs are OUT OF SYNC (scripts/cf/check_status_docs.py):", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    print("Fix the docs from the task list (the source of truth); push the deployed page with "
          "scripts/cf/sync_status_page.py --push.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
