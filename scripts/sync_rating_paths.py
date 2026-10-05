#!/usr/bin/env python3
"""Keep the deployed GL and CF Rating Paths pages in sync with GL_Algorithm/ and CF_Algorithm/ (user, 2026-10-02).

The deployed copies live in the Federato/Ideation repo as two artifacts of the iso-rating-engine project and Vercel
publishes them at https://federato-ideation.vercel.app/iso-rating-engine/gl-rating-paths/ and .../cf-rating-paths/.
Each page is the local explainer wrapped in Ideation's page shell: a full document (a bare fragment such as
gl-rating-chains.html gets a <head>), a top pad for the chrome bar, and the mandatory shared chrome tag before </body>
(Ideation's CLAUDE.md). Which local file becomes which page, in what order and with what name, is PAGES below.

    python scripts/sync_rating_paths.py --check     # does origin/trunk carry exactly these pages? (exit 1 if not)
    python scripts/sync_rating_paths.py --push      # if not: branch from origin/trunk in a temporary worktree, write the
                                                    # pages and artifact.json, bump "updated", commit, push, open the PR
                                                    # and merge it (same shape as scripts/cf/sync_status_page.py)

Regenerate the generated explainers first (scripts/premium/0*_*.py, scripts/build_backlog_html.py) so what you
publish is current.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDEATION = Path(r"F:\Ideation")
PROJECT = "iso-rating-engine"
SITE = "https://federato-ideation.vercel.app"
PAD = "<style>body{padding-top:44px}</style>\n"

# artifact slug -> (artifact name, local folder, [(published file, local file, page name, description or None), ...])
PAGES = {
    "gl-rating-paths": ("GL Rating Paths", "GL_Algorithm", [
        ("index.html", "GL_Premium_Map.html", "Premium map",
         "How every GL premium rolls up to the policy total, by edition."),
        ("premium-tree.html", "GL_Premium_Tree.html", "Premium tree",
         "Every premium-producing coverage group in the GL corpus, generated from the rule files."),
        ("account-premium.html", "GL_Account_Premium_Bracket.html", "Account premium",
         "A two-location, three-class account priced in the engine, subtotal by subtotal."),
        ("rating-chains.html", "gl-rating-chains.html", "Rating chains",
         "Step-by-step rating chain for each subline, with edition branches."),
        ("premops-products-trace.html", "GL_PremOps_Prods_Premium_Trace.html", "Prem/Ops & Products trace",
         "The Premises/Operations and Products/Completed Operations calculation, rule by rule."),
        ("premops-products-plain.html", "GL_PremOps_Prods_Premium_Trace_PlainEnglish.html", "Trace, plain English", None),
        ("scenario-buildup.html", "GL_Scenario_Premium_Buildup.html", "Scenario build-up",
         "One Oklahoma liquor-licensed shop priced end to end in the engine."),
        ("scenario-plain.html", "GL_Scenario_Premium_Buildup_PlainEnglish.html", "Scenario, plain English", None),
    ]),
    "cf-rating-paths": ("CF Rating Paths", "CF_Algorithm", [
        ("index.html", "CF_Premium_Map.html", "Premium map",
         "How every Property premium rolls up to the account total."),
        ("premium-tree.html", "CF_Premium_Tree.html", "Premium tree",
         "All 546 premium rules in the countrywide package and where states rewrite them, generated from the rule files."),
        ("account-premium.html", "CF_Account_Premium_Bracket.html", "Account premium",
         "How an account premium is assembled, with chunk 14's ISO-confirmed total."),
        ("rating-path-switches.html", "CF_RatingPath_Switches.html", "Rating path switches",
         "Which inputs switch between cause-of-loss forms, class vs specific rating, blanket and the other paths, "
         "with the chunk that built each."),
        ("required-inputs.html", "CF_Required_Submission_Inputs.html", "Required inputs",
         "What a submission must carry, what the engine derives, and the inputs found in chunks 11 to 27."),
        ("rating-chains.html", "cf-rating-chains.html", "Rating chains",
         "Step-by-step rating chain for each coverage and cause-of-loss form."),
    ]),
}


def git(*args, cwd=IDEATION, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout


def wrap(html: str, slug: str, title: str) -> str:
    """The local page as an Ideation page: full document, chrome pad, and the shared chrome tag before </body>."""
    tag = f'<script src="/shared/chrome.js" data-project="{PROJECT}" data-artifact="{slug}"></script>'
    html = html.replace("\r\n", "\n")
    if "/shared/chrome.js" not in html:
        if re.search(r"<body[\s>]", html, re.I):
            i = html.lower().rfind("</body>")
            html = (html[:i] + tag + "\n" + html[i:]) if i >= 0 else html + "\n" + tag + "\n"
        else:  # a bare fragment: give it a head; its own <title> / charset lines move there
            m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
            t = m.group(1).strip() if m else title
            body = "\n".join(l for l in html.split("\n")
                             if not re.match(r"\s*(<title>.*</title>|<meta charset=[\"']?utf-8[\"']?>)\s*$", l, re.I))
            html = ('<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n'
                    '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
                    f'  <title>{t}</title>\n  <link rel="icon" type="image/png" href="/favicon.png" />\n'
                    f'</head>\n<body>\n{body.strip()}\n{tag}\n</body>\n</html>\n')
    i = html.lower().rfind("</head>")
    return html[:i] + PAD + html[i:]


def artifact_json(slug: str, old: dict | None, today: str) -> dict:
    name, _, pages = PAGES[slug]
    aj = dict(old or {"slug": slug, "type": "document", "status": "exploration"})
    aj["name"] = name
    aj["pages"] = [dict({"file": out, "name": n}, **({"description": d} if d else {})) for out, _, n, d in pages]
    aj.setdefault("updated", today)
    aj.setdefault("updatedBy", "Dan")
    return aj


def wanted() -> dict[str, str]:
    """published repo path -> content, for every page."""
    out = {}
    for slug, (name, folder, pages) in PAGES.items():
        for pub, local, pname, _ in pages:
            src = ROOT / folder / local
            out[f"projects/{PROJECT}/{slug}/{pub}"] = wrap(src.read_text(encoding="utf-8"), slug, f"{pname} — {name}")
    return out


def drift() -> list[str]:
    """Repo paths whose origin/trunk copy differs from what this script would write (pages and page lists)."""
    git("fetch", "-q", "origin", "trunk")
    bad = []
    for rel, text in wanted().items():
        r = subprocess.run(["git", "show", f"origin/trunk:{rel}"], cwd=IDEATION, capture_output=True, text=True,
                           encoding="utf-8")
        if r.returncode != 0 or r.stdout.replace("\r\n", "\n") != text:
            bad.append(rel)
    for slug in PAGES:
        rel = f"projects/{PROJECT}/{slug}/artifact.json"
        r = subprocess.run(["git", "show", f"origin/trunk:{rel}"], cwd=IDEATION, capture_output=True, text=True,
                           encoding="utf-8")
        old = json.loads(r.stdout) if r.returncode == 0 else None
        if old is None or {k: old.get(k) for k in ("name", "pages")} != {k: artifact_json(slug, old, "")[k] for k in ("name", "pages")}:
            bad.append(rel)
    return bad


def push() -> int:
    bad = drift()
    if not bad:
        print(f"rating paths already in sync ({SITE}/{PROJECT}/gl-rating-paths/, .../cf-rating-paths/)")
        return 0
    today = dt.date.today().isoformat()
    branch = f"dan/rating-paths-sync-{today}-{dt.datetime.now().strftime('%H%M%S')}"
    tmp = Path(tempfile.mkdtemp(prefix="ideation-sync-"))
    wt = tmp / "wt"
    git("worktree", "add", "-q", "-b", branch, str(wt), "origin/trunk")
    try:
        pj_path = wt / "projects" / PROJECT / "project.json"
        pj = json.loads(pj_path.read_text(encoding="utf-8"))
        for rel, text in wanted().items():
            p = wt / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8", newline="\n")
        for slug in PAGES:
            p = wt / "projects" / PROJECT / slug / "artifact.json"
            old = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
            aj = artifact_json(slug, old, today)
            if any(r.startswith(f"projects/{PROJECT}/{slug}/") for r in bad):
                aj["updated"], aj["updatedBy"] = today, "Dan"
            p.write_text(json.dumps(aj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            if slug not in pj.setdefault("artifacts", []):
                pj["artifacts"].append(slug)
        pj["updated"], pj["updatedBy"] = today, "Dan"
        pj_path.write_text(json.dumps(pj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        git("add", "-A", f"projects/{PROJECT}", cwd=wt)
        title = f"Sync GL and CF Rating Paths ({today})"
        git("commit", "-q", "-m", f"{title}\n\nMirrors Recursive_Harness_2.0/GL_Algorithm and CF_Algorithm explainers.\n\n"
                                  + "\n".join(bad) + "\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>", cwd=wt)
        git("push", "-q", "-u", "origin", branch, cwd=wt)
        pr = subprocess.run(["gh", "pr", "create", "--repo", "Federato/Ideation", "--base", "trunk", "--head", branch,
                             "--title", title,
                             "--body", "Mirrors the rating-path explainers in Recursive_Harness_2.0 "
                                       "(`scripts/sync_rating_paths.py`).\n\n- " + "\n- ".join(bad)
                                       + "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"],
                            cwd=wt, capture_output=True, text=True, encoding="utf-8")
        if pr.returncode != 0:
            raise RuntimeError(f"gh pr create: {pr.stderr.strip()[:300]}")
        url = pr.stdout.strip().splitlines()[-1]
        mg = subprocess.run(["gh", "pr", "merge", url, "--merge", "--delete-branch"], cwd=wt, capture_output=True,
                            text=True, encoding="utf-8")
        if mg.returncode != 0:
            raise RuntimeError(f"gh pr merge {url}: {mg.stderr.strip()[:300]}")
        print(f"synced: {url} merged into trunk ({len(bad)} file(s)); Vercel deploys {SITE}/{PROJECT}/")
        return 0
    finally:
        git("worktree", "remove", "--force", str(wt), check=False)
        shutil.rmtree(tmp, ignore_errors=True)
        git("branch", "-D", branch, check=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--push", action="store_true")
    a = ap.parse_args()
    if a.check:
        bad = drift()
        print("RATING PATHS IN SYNC" if not bad else "RATING PATHS OUT OF SYNC:\n  " + "\n  ".join(bad))
        return 0 if not bad else 1
    return push()


if __name__ == "__main__":
    raise SystemExit(main())
