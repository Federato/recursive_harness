#!/usr/bin/env python3
"""Mirror docs/CF-BUILD-STATUS.html into the Federato Ideation repo.

docs/CF-BUILD-STATUS.html stays the one page that gets edited. This script
copies it to the Ideation artifact (iso-rating-engine / cf-build-status),
wrapped as an Ideation page (doctype, head, the shared chrome tag), bumps the
artifact's and project's `updated` / `updatedBy`, then opens a PR to trunk on a
fresh branch. Merging the PR is left to you.

    python scripts/sync_build_status_to_ideation.py              # copy + PR
    python scripts/sync_build_status_to_ideation.py --no-pr      # copy only
    python scripts/sync_build_status_to_ideation.py --ideation D:/repos/Ideation --by Dan

Exits 0 with "no changes" when the Ideation copy is already current.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "CF-BUILD-STATUS.html"
DEFAULT_IDEATION = Path("F:/Ideation")
PROJECT, ARTIFACT = "iso-rating-engine", "cf-build-status"

HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CF Build Status — ISO Rating Engine</title>
  <link rel="icon" type="image/png" href="/favicon.png" />
</head>
<body>
"""
TAIL = f"""
<script src="/shared/chrome.js" data-project="{PROJECT}" data-artifact="{ARTIFACT}"></script>
</body>
</html>
"""
# The source is a bare fragment: it opens with <title> + <meta charset> and
# repeats the <title> at the end. Those lines move into the wrapper's <head>.
DROP = re.compile(r"^\s*(<title>.*</title>|<meta charset=[\"']?utf-8[\"']?>)\s*$", re.I)


def wrap(src: str) -> str:
    body = "\n".join(l for l in src.splitlines() if not DROP.match(l)).strip("\n")
    return HEAD + body + "\n" + TAIL


def bump(json_path: Path, today: str, by: str) -> None:
    # Regex, not json.dump, so the manifest's formatting (and the diff) stays small.
    text = json_path.read_text(encoding="utf-8")
    text = re.sub(r'("updated"\s*:\s*)"[^"]*"', rf'\g<1>"{today}"', text, count=1)
    text = re.sub(r'("updatedBy"\s*:\s*)"[^"]*"', rf'\g<1>"{by}"', text, count=1)
    json_path.write_text(text, encoding="utf-8", newline="\n")


def git(repo: Path, *args: str, capture: bool = False) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], text=True,
                       capture_output=capture, check=True)
    return (r.stdout or "").strip()


def find_gh() -> str:
    gh = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"
    if not Path(gh).exists() and not shutil.which(gh):
        sys.exit("gh CLI not found; install it or rerun with --no-pr")
    return gh


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ideation", type=Path, default=DEFAULT_IDEATION, help="Ideation repo path")
    ap.add_argument("--by", default="Dan", help="updatedBy name (default: Dan)")
    ap.add_argument("--no-pr", action="store_true", help="copy into Ideation only; no git")
    a = ap.parse_args()

    repo = a.ideation.resolve()
    art_dir = repo / "projects" / PROJECT / ARTIFACT
    page = art_dir / "index.html"
    if not page.exists():
        sys.exit(f"{page} not found -- is --ideation right?")

    if not a.no_pr:
        if git(repo, "status", "--porcelain", capture=True):
            sys.exit(f"{repo} has uncommitted changes; commit or stash them first")
        git(repo, "checkout", "-q", "trunk")
        git(repo, "pull", "-q")

    new = wrap(SOURCE.read_text(encoding="utf-8"))
    old = page.read_text(encoding="utf-8").replace("\r\n", "\n")
    if new == old:
        print("no changes: the Ideation copy already matches docs/CF-BUILD-STATUS.html")
        return

    today = dt.date.today().isoformat()
    page.write_text(new, encoding="utf-8", newline="\n")
    bump(art_dir / "artifact.json", today, a.by)
    bump(repo / "projects" / PROJECT / "project.json", today, a.by)
    print(f"copied -> {page}")

    if a.no_pr:
        print("--no-pr: left uncommitted in the Ideation repo")
        return

    branch = f"dan/cf-build-status-sync-{dt.datetime.now():%Y-%m-%d-%H%M}"
    title = f"Sync CF Build Status ({today})"
    git(repo, "checkout", "-q", "-b", branch)
    git(repo, "add", f"projects/{PROJECT}")
    git(repo, "commit", "-q", "-m", title,
        "-m", "Mirrors Recursive_Harness_2.0/docs/CF-BUILD-STATUS.html.")
    git(repo, "push", "-q", "-u", "origin", branch)
    r = subprocess.run([find_gh(), "pr", "create", "--base", "trunk", "--head", branch,
                        "--title", title,
                        "--body", "Mirrors `Recursive_Harness_2.0/docs/CF-BUILD-STATUS.html` "
                                  "via `scripts/sync_build_status_to_ideation.py`."],
                       cwd=repo, text=True, capture_output=True)
    git(repo, "checkout", "-q", "trunk")
    if r.returncode:
        sys.exit(f"pushed {branch} but PR creation failed:\n{r.stderr}")
    print(f"PR opened: {r.stdout.strip()}")
    print("merge it on GitHub, or:  gh pr merge --merge --delete-branch <number>")


if __name__ == "__main__":
    main()
