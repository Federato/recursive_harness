#!/usr/bin/env python3
"""TC-38 (D6): write the console's read-only snapshot, one self-contained HTML page, for Ideation. No ISO calls.

    python scripts/tc/tc38_snapshot.py [--out results/tc/snapshot/index.html]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
os.environ["TC_DISPATCH"] = "0"                               # a snapshot never starts the dispatcher

from ui import console_page  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "tc" / "snapshot" / "index.html")
    a = ap.parse_args()
    html = console_page.snapshot()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(html, encoding="utf-8")
    print(f"wrote {a.out} ({len(html) / 1_048_576:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
