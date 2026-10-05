#!/usr/bin/env python3
"""Keep the deployed CF Build Status page in sync with docs/CF-BUILD-STATUS.html (user, 2026-10-01).

The deployed copy lives in the Federato/Ideation repo at projects/iso-rating-engine/cf-build-status/index.html and Vercel
publishes it at https://federato-ideation.vercel.app/iso-rating-engine/cf-build-status/. It is the local page wrapped in
Ideation's page shell: <!doctype>, a <head> with the Ideation title and favicon, and the mandatory shared chrome tag
before </body> (Ideation's CLAUDE.md: every artifact page must end with it). The body is the local page verbatim.

    python scripts/cf/sync_status_page.py --check     # is origin/trunk's copy the local page? (exit 1 if not)
    python scripts/cf/sync_status_page.py --push      # if not: branch from origin/trunk in a temporary worktree, write the page,
                                                      # bump artifact.json / project.json "updated", commit, push, open the PR
                                                      # and merge it (the same shape as PR #616); the user's checkout untouched
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "docs" / "CF-BUILD-STATUS.html"
IDEATION = Path(r"F:\Ideation")
REL = "projects/iso-rating-engine/cf-build-status/index.html"
ART = "projects/iso-rating-engine/cf-build-status/artifact.json"
PROJ = "projects/iso-rating-engine/project.json"
URL = "https://federato-ideation.vercel.app/iso-rating-engine/cf-build-status/"
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '  <title>CF Build Status — ISO Rating Engine</title>\n  <link rel="icon" type="image/png" href="/favicon.png" />\n'
        '</head>\n<body>\n')
TAIL = '\n<script src="/shared/chrome.js" data-project="iso-rating-engine" data-artifact="cf-build-status"></script>\n</body>\n</html>\n'


def git(*args, cwd=IDEATION, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout


def body(text: str) -> str:
    """the local page minus its own <title> / <meta charset> lines (the shell supplies the head)."""
    lines = text.replace("\r\n", "\n").split("\n")
    return "\n".join(x for x in lines if not re.match(r"\s*<title>.*</title>\s*$|\s*<meta charset=", x)).strip("\n")


def wrapped() -> str:
    return HEAD + body(LOCAL.read_text(encoding="utf-8")) + "\n" + TAIL


def unwrap(deployed: str) -> str:
    d = deployed.replace("\r\n", "\n")
    d = d.split("<body>\n", 1)[1] if "<body>\n" in d else d
    d = d.split('<script src="/shared/chrome.js"', 1)[0]
    return d.strip("\n")


def deployed_in_sync():
    """(same, reason) comparing origin/trunk's deployed page with the local page's body."""
    git("fetch", "-q", "origin", "trunk")
    deployed = git("show", f"origin/trunk:{REL}")
    a, b = unwrap(deployed), body(LOCAL.read_text(encoding="utf-8"))
    if a == b:
        return True, "same body"
    al, bl = a.split("\n"), b.split("\n")
    diff = sum(1 for x, y in zip(al, bl) if x != y) + abs(len(al) - len(bl))
    return False, f"{diff} line(s) differ"


def push():
    same, why = deployed_in_sync()
    if same:
        print(f"deployed page already in sync ({URL})")
        return 0
    today = dt.date.today().isoformat()
    branch = f"dan/cf-build-status-sync-{today}-{dt.datetime.now().strftime('%H%M')}"
    tmp = Path(tempfile.mkdtemp(prefix="ideation-sync-"))
    wt = tmp / "wt"
    git("worktree", "add", "-q", "-b", branch, str(wt), "origin/trunk")
    try:
        (wt / REL).write_text(wrapped(), encoding="utf-8", newline="\n")
        for rel in (ART, PROJ):
            p = wt / rel
            j = json.loads(p.read_text(encoding="utf-8"))
            j["updated"], j["updatedBy"] = today, "Dan"
            p.write_text(json.dumps(j, indent=2) + "\n", encoding="utf-8", newline="\n")
        git("add", REL, ART, PROJ, cwd=wt)
        git("commit", "-q", "-m", f"Sync CF Build Status ({today})\n\nMirrors Recursive_Harness_2.0/docs/CF-BUILD-STATUS.html.\n\n"
                                  "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>", cwd=wt)
        git("push", "-q", "-u", "origin", branch, cwd=wt)
        pr = subprocess.run(["gh", "pr", "create", "--repo", "Federato/Ideation", "--base", "trunk", "--head", branch,
                             "--title", f"Sync CF Build Status ({today})",
                             "--body", "Mirrors Recursive_Harness_2.0/docs/CF-BUILD-STATUS.html (status page sync).\n\n"
                                       "🤖 Generated with [Claude Code](https://claude.com/claude-code)"],
                            cwd=wt, capture_output=True, text=True, encoding="utf-8")
        if pr.returncode != 0:
            raise RuntimeError(f"gh pr create: {pr.stderr.strip()[:300]}")
        url = pr.stdout.strip().splitlines()[-1]
        mg = subprocess.run(["gh", "pr", "merge", url, "--merge", "--delete-branch"], cwd=wt, capture_output=True, text=True, encoding="utf-8")
        if mg.returncode != 0:
            raise RuntimeError(f"gh pr merge {url}: {mg.stderr.strip()[:300]}")
        print(f"synced: {url} merged into trunk ({why}); Vercel deploys {URL}")
        return 0
    finally:
        git("worktree", "remove", "--force", str(wt), check=False)
        shutil.rmtree(tmp, ignore_errors=True)
        git("branch", "-D", branch, check=False)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--push", action="store_true")
    a = ap.parse_args()
    if a.check:
        same, why = deployed_in_sync()
        print(("DEPLOYED PAGE IN SYNC" if same else f"DEPLOYED PAGE OUT OF SYNC: {why}") + f" ({URL})")
        return 0 if same else 1
    return push()


if __name__ == "__main__":
    raise SystemExit(main())
