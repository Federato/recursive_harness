#!/usr/bin/env python3
"""Are the Property status documents in sync with each other? (user, 2026-10-01: "make sure this is always in sync")

For every chunk whose task list (docs/CF-CHUNKnn-TASKS.md) numbers its tasks Cnn-xx, the task list is the source of truth:
  1. its **Status:** line states "<done> of <total>" (done = rows marked ✅, total = task rows)
  2. docs/CF-BUILD-STATUS.html marks exactly the same task ids done (&#9989;) in that chunk's section
  3. every RC label there ("RC-k ... (n) ... k of n done") matches the rows of the table under it
  4. the chunk's tag in its section, its row in the "remaining" table and its row in the plan table say "<done> of <total>"
  5. docs/CF-START-HERE.md's first "Pick up here" block names every OPEN chunk's "<done> of <total>"
And the deployed copy (Federato/Ideation, projects/iso-rating-engine/cf-build-status/index.html on origin/trunk) carries the
same body as docs/CF-BUILD-STATUS.html (sync_status_page.py --check; skipped with --no-deployed or when offline).

    python scripts/cf/check_status_docs.py [--no-deployed]

Exits 1 on any disagreement, listing each.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
DONE, TODO = "&#9989;", "&#11036;"


def chunk_tasks(n: int, text: str):
    rows = re.findall(rf"^\| (C{n}-\d\d) \|(.*)$", text, re.M)
    # the status cell is the second after the id (| id | task | status | notes |); older lists write "✅ Done ..." there
    done = {tid for tid, rest in rows if len(rest.split("|")) > 1 and rest.split("|")[1].strip().startswith("✅")}
    return [tid for tid, _ in rows], done


def section(html: str, n: int):
    m = re.search(rf'<h3><span class="n">{n}</span>', html)
    if not m:
        return None
    nxt = re.search(r'<h3><span class="n">\d+</span>', html[m.end():])
    nxt2 = html.find('<h2 id="remaining">', m.end())
    end = m.end() + nxt.start() if nxt else len(html)
    if nxt2 != -1 and nxt2 < end and nxt2 > m.end():
        end = nxt2
    return html[m.start():end]


def says(text: str, k: int, total: int) -> bool:
    """'<k> of <total>', or for a finished chunk the older phrasing 'all <total> tasks'."""
    return f"{k} of {total}" in text or (k == total and f"all {total} tasks" in text)


def check(deployed: bool = True) -> list[str]:
    problems = []
    html = (DOCS / "CF-BUILD-STATUS.html").read_text(encoding="utf-8")
    start = (DOCS / "CF-START-HERE.md").read_text(encoding="utf-8")
    pick = start.split("## Pick up here", 1)[1].split("\n## ", 1)[0] if "## Pick up here" in start else ""
    chunks = []
    for f in sorted(DOCS.glob("CF-CHUNK*-TASKS.md"), key=lambda p: int(re.search(r"\d+", p.name).group())):
        n = int(re.search(r"\d+", f.name).group())
        text = f.read_text(encoding="utf-8")
        ids, done = chunk_tasks(n, text)
        if not ids:
            continue
        chunks.append(n)
        total, k = len(ids), len(done)
        st = re.search(r"^\*\*Status:([^\n]*)", text, re.M)
        status = st.group(1) if st else ""
        if st and not says(status, k, total):          # chunks 9 and 10 predate the Status line
            problems.append(f"chunk {n}: task list Status line does not say '{k} of {total}': {status[:90]!r}")
        sec = section(html, n)
        if sec is None:
            problems.append(f"chunk {n}: no section on CF-BUILD-STATUS.html")
            continue
        html_done = set(re.findall(rf'<td class="st">{DONE}</td><td class="num">(C{n}-\d\d)</td>', sec))
        html_all = set(re.findall(rf'<td class="num">(C{n}-\d\d)</td>', sec))
        if html_all and html_all != set(ids):
            problems.append(f"chunk {n}: status page lists tasks {sorted(html_all ^ set(ids))[:6]} differently from the task list")
        if html_done != done:
            problems.append(f"chunk {n}: done on the task list but not the page {sorted(done - html_done)}; on the page but not the list {sorted(html_done - done)}")
        for lab in re.finditer(r'<span class="lab">(RC-\d+) &middot;[^<]*?\((\d+)\) &middot; (\d+) of (\d+) done', sec):
            rc, n_rows, k_lab, n_lab = lab.group(1), int(lab.group(2)), int(lab.group(3)), int(lab.group(4))
            table = sec[lab.end():].split("</table>", 1)[0]
            rows = re.findall(rf'<td class="st">([^<]*)</td><td class="num">C{n}-\d\d</td>', table)
            k_rows = sum(1 for x in rows if x == DONE)
            if len(rows) != n_rows or k_rows != k_lab or n_lab != n_rows:
                problems.append(f"chunk {n} {rc}: label says {k_lab} of {n_lab} ({n_rows}); its table has {k_rows} done of {len(rows)}")
        gated = "GATED" in status.upper()
        tag = re.search(r'<h3><span class="n">\d+</span>[^<]*<span class="tag[^"]*">([^<]*)</span>', sec)
        if tag and not says(tag.group(1), k, total):
            problems.append(f"chunk {n}: section tag {tag.group(1)!r} does not say '{k} of {total}'")
        for label, pat in (("remaining-table row", rf'<tr><td class="num">{n}</td><td>[^<]*</td><td><span class="tag[^"]*">([^<]*)</span>'),
                           ("plan-table row", rf'<tr(?: class="d")?><td class="num">{n}</td><td>[^<]*<b>\(([^)]*)\)</b>')):
            mm = re.search(pat, html)
            if mm and "of" in mm.group(1) and not says(mm.group(1), k, total):
                problems.append(f"chunk {n}: {label} {mm.group(1)!r} does not say '{k} of {total}'")
        if not gated and "OPEN" in status.upper() and f"{k} of {total}" not in pick:
            problems.append(f"chunk {n} is OPEN at {k} of {total}, but CF-START-HERE's 'Pick up here' block does not say so")
    if deployed:
        try:
            sync = __import__("sync_status_page")
            same, why = sync.deployed_in_sync()
            if not same:
                problems.append(f"deployed page (Federato/Ideation origin/trunk) differs from docs/CF-BUILD-STATUS.html: {why} "
                                f"-- run scripts/cf/sync_status_page.py --push")
        except Exception as exc:                          # offline / no Ideation checkout: report, do not fail the docs check
            print(f"  (deployed copy not checked: {type(exc).__name__}: {str(exc)[:100]})")
    print(f"status documents checked for chunks {chunks[0]}-{chunks[-1]} ({len(chunks)} task lists)" if chunks else "no task lists found")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-deployed", action="store_true")
    a = ap.parse_args()
    problems = check(deployed=not a.no_deployed)
    for p in problems:
        print(f"  OUT OF SYNC: {p}")
    print("STATUS DOCS IN SYNC" if not problems else f"{len(problems)} disagreement(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
