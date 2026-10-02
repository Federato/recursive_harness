#!/usr/bin/env python3
"""Chunk 28, C28-01: the opening census. Nothing owned by chunk 28 left out of its feature sets.

Enumerates, rather than trusting the plan card:
  1. every CF open item (OI-86 on) in docs/OPEN-ITEMS.md not CLOSED / FIXED / MERGED / DECIDED, with its status word;
  2. every OI id mentioned within a line that names "chunk 28" in docs/*.md (gate files, task lists, resume page);
  3. the status page's cross-chunk rows still tagged open;
then checks each OI found in 1 or 2 against the feature-set table of docs/CF-CHUNK28-TASKS.md: assigned, or MISSING.
GL items (OI-87..OI-98 and below OI-86) are listed apart: not Property's.

    python scripts/cf/909_chunk28_census.py      (log: results/cf-raas/logs/chunk28_census.log)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
LOG = ROOT / "results" / "cf-raas" / "logs" / "chunk28_census.log"
GL_RANGE = range(87, 99)          # the GL rows between the CF ones (OI-87 .. OI-98)
SHUT = re.compile(r"`(CLOSED|FIXED|RESOLVED|MERGED|DECIDED)")


def out(lines, s=""):
    print(s)
    lines.append(s)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    lines = []
    reg = {}
    for l in (DOCS / "OPEN-ITEMS.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| \*\*OI-(\d+)\*\* \| \*\*(.*?)\*\* \| (.*?) \|", l)
        if m and int(m.group(1)) >= 86:
            n, title, st = int(m.group(1)), m.group(2), m.group(3)
            shut = bool(SHUT.search(st[:160])) or "Merged" in st[:200] or "MERGED" in st[:200]
            reg[n] = (title, st, shut)
    open_cf = {n: v for n, v in reg.items() if not v[2] and n not in GL_RANGE}
    open_gl = {n: v for n, v in reg.items() if not v[2] and n in GL_RANGE}
    out(lines, f"1. register: {len(reg)} items from OI-86; open, Property: {len(open_cf)}; open, GL (not Property's): {len(open_gl)}")
    for n, (t, st, _) in sorted(open_cf.items()):
        out(lines, f"   OI-{n:<4d} {re.sub(r'[`*]', '', st)[:28]:28s} {t[:110]}")

    mentions = {}
    for f in sorted(DOCS.glob("*.md")):
        if f.name == "CF-CHUNK28-TASKS.md":
            continue
        for l in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.search(r"chunk 28|chunk 28's|Chunk 28", l):
                for oi in re.findall(r"OI-(\d+)", l):
                    if int(oi) >= 86 and int(oi) not in GL_RANGE:
                        mentions.setdefault(int(oi), set()).add(f.name)
    out(lines, f"\n2. OI ids on a line that names chunk 28, in {len(list(DOCS.glob('*.md')))} docs: {len(mentions)}")
    for n in sorted(mentions):
        state = "open" if n in open_cf else ("closed/merged" if n in reg else "not in register")
        out(lines, f"   OI-{n:<4d} {state:15s} {', '.join(sorted(mentions[n]))[:110]}")

    page = (DOCS / "CF-BUILD-STATUS.html").read_text(encoding="utf-8")
    rows = re.findall(r'<tr><td>([^<]+)</td><td><span class="tag (open|warn)">([^<]*)</span>', page)
    out(lines, f"\n3. status page cross-chunk rows still open: {len(rows)}")
    for name, _, tag in rows:
        out(lines, f"   {name[:60]:60s} {tag[:60]}")

    plan = (DOCS / "CF-CHUNK28-TASKS.md").read_text(encoding="utf-8")
    sets = plan[plan.find("## The feature sets"):plan.find("## Tasks")]
    assigned = {int(x) for x in re.findall(r"OI-(\d+)", sets)}
    want = set(open_cf) | {n for n in mentions if n in open_cf}
    missing = sorted(want - assigned)
    out(lines, f"\n4. open Property items assigned to a feature set: {len(want & assigned)} of {len(want)}"
               + (f"; MISSING: {', '.join(f'OI-{n}' for n in missing)}" if missing else "; none missing"))
    stale = sorted(n for n in assigned if n in reg and reg[n][2])
    if stale:
        out(lines, f"   assigned but closed in the register (check): {', '.join(f'OI-{n}' for n in stale)}")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
