#!/usr/bin/env python3
"""Chunk 27 opening census -- open gate points and open items on closed chunks.

Chunk 27 has no coverage family: it is the loose ends of chunks already closed.
The plan card lists five rows; this census enumerates rather than trusting it:

  1  Gates: every docs/CF-CHUNK*-GATE*.md -- its overall score line and every
     scorecard row (or line) marked not passed, partial, outstanding or open.
  2  Open items: every OI row in docs/OPEN-ITEMS.md with its status word, and
     any OI number mentioned in the CF docs that has no register row.
  3  The resume page's standing gaps: the per-state gaps table and every
     "Open:" / "open" note in CF-START-HERE.md.
  4  The status page's "Open items that cross every chunk" section and every
     unchecked task row inside a card whose chunk is closed / gated.

    python scripts/cf/908_chunk27_census.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import collections
import html
import re
import sys
from pathlib import Path

# the docs carry symbols (⬜ ✅) the Windows console code page cannot encode: write UTF-8 (2026-10-02 refresh crashed without it)
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
NOT_PASSED = re.compile(r"❌|⚠|⬜|&#11036;|\bnot passed\b|\bpartial\b|\boutstanding\b|\bopen\b|\bOPEN\b|\bnot yet\b", re.I)


def plain(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def main():
    # 1 gates
    print("[1/4] gate files: score line and rows not passed", flush=True)
    gates = sorted(DOCS.glob("CF-CHUNK*-GATE*.md"), key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p.name)])
    for g in gates:
        t = g.read_text(encoding="utf-8")
        score = re.search(r"(\*\*)?(\d) of 9(\*\*)?[^\n]{0,110}", t)
        print(f"\n  {g.name}: {plain(score.group(0)) if score else 'no \"N of 9\" score line'}")
        rows = [ln for ln in t.splitlines() if ln.startswith("|") and NOT_PASSED.search(ln)
                and not re.match(r"\|\s*-", ln)]
        for ln in rows[:14]:
            print(f"      {plain(ln)[:230]}")
        if len(rows) > 14:
            print(f"      ... {len(rows) - 14} more")

    # 2 open items
    print("\n[2/4] open-items register (docs/OPEN-ITEMS.md), OI-100 onwards", flush=True)
    reg = (DOCS / "OPEN-ITEMS.md").read_text(encoding="utf-8")
    rows = {}
    for ln in reg.splitlines():
        m = re.match(r"\|\s*\*\*(OI-1\d\d)\*\*\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", ln)
        if m:
            status = re.search(r"`([A-Z]+)`", m.group(3))
            rows[m.group(1)] = (status.group(1) if status else "?", plain(m.group(2))[:150], plain(m.group(3))[:150])
    for oi, (st, title, note) in sorted(rows.items()):
        print(f"  {oi} [{st:8s}] {title}")
        if st != "CLOSED":
            print(f"           {note}")
    mentioned = set()
    for p in list(DOCS.glob("*.md")) + list(DOCS.glob("*.html")) + list((ROOT / "CF_Algorithm").glob("*.md")):
        mentioned |= set(re.findall(r"OI-1\d\d", p.read_text(encoding="utf-8", errors="replace")))
    missing = sorted(mentioned - set(rows))
    print(f"  OI numbers mentioned in CF docs with NO register row: {missing or 'none'}")
    for oi in missing:
        for p in sorted(DOCS.glob("*.md")):
            t = p.read_text(encoding="utf-8")
            m = re.search(rf"[^\n]{{0,120}}{oi}[^\n]{{0,160}}", t)
            if m:
                print(f"    {oi} first in {p.name}: {plain(m.group(0))[:260]}")
                break

    # 3 resume page
    print("\n[3/4] CF-START-HERE.md: per-state gaps and 'Open' notes", flush=True)
    sh = (DOCS / "CF-START-HERE.md").read_text(encoding="utf-8")
    for ln in sh.splitlines():
        if ln.startswith("|") and re.search(r"gap|missing|untraced|empty|open|not built|backlog", ln, re.I) \
                and not re.match(r"\|\s*-", ln):
            print(f"  TABLE {plain(ln)[:240]}")
    for m in re.finditer(r"[^.\n]*\b(Open|open, not blocking|Open, not blocking|waits? on|still open)\b[^.\n]*[.\n]", sh):
        s = plain(m.group(0))
        if len(s) > 25:
            print(f"  NOTE  {s[:240]}")

    # 4 status page
    print("\n[4/4] CF-BUILD-STATUS.html: cross-chunk open items, and unchecked rows in closed cards", flush=True)
    st = (DOCS / "CF-BUILD-STATUS.html").read_text(encoding="utf-8")
    i = st.find("<h2>Open items that cross every chunk</h2>")
    if i >= 0:
        sec = st[i:st.find("<h2", i + 10)]
        for r in re.findall(r"<tr>(.*?)</tr>", sec, re.S):
            print(f"  CROSS {plain(r)[:240]}")
    for card in re.finditer(r'<div class="chunk (done|now|todo)">(.*?)</div>', st, re.S):
        kind, body = card.groups()
        if kind != "done":
            continue
        head = plain(re.search(r"<h3>(.*?)</h3>", body, re.S).group(1))[:70]
        opens = [plain(r) for r in re.findall(r"<tr>(.*?)</tr>", body, re.S) if "&#11036;" in r or "⬜" in r]
        if opens:
            print(f"  CARD {head}: {len(opens)} unchecked")
            for o in opens[:6]:
                print(f"      {o[:220]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
