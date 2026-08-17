#!/usr/bin/env python
"""Render the plain-English backlog into one self-contained HTML page.

    python scripts/build_backlog_html.py

Output: docs/backlog_20260817.html  (no external assets, opens offline)

**Reuses `build_docs_html.CSS` rather than restating it.** A second stylesheet
would drift from the first, and a review document that looks unlike every other
document in the project reads as if it came from somewhere else.
"""
import datetime
import html
import importlib.util
import os
import re
import sys

import markdown

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE = "docs/WHATS-LEFT-PLAIN-ENGLISH.md"
OUT = "docs/backlog_20260817.html"
TITLE = "What's left — 17 August 2026"
SUBTITLE = ("ISO General Liability Rating Engine · Recursive Harness 2.0 · "
            "the backlog in plain English")

EXT = ["tables", "fenced_code", "toc", "sane_lists", "attr_list"]


def house_css() -> str:
    """The CSS the rest of the docs already use."""
    spec = importlib.util.spec_from_file_location(
        "_docs_html", os.path.join(ROOT, "scripts", "build_docs_html.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CSS


EXTRA = """
.wrap{display:block;max-width:60rem;margin:0 auto;padding:0 1.5rem 5rem}
article{max-width:none}
.toc-box{border:1px solid var(--line);border-radius:8px;padding:1rem 1.25rem;
margin:1.5rem 0 2.5rem;background:#fff}
.toc-box .lbl{font-weight:600;color:var(--accent);margin-bottom:.4rem}
.toc-box ul{margin:.2rem 0;padding-left:1.1rem}
.toc-box>ul>li{margin:.15rem 0}
h2{margin-top:2.6rem;padding-top:1.4rem;border-top:1px solid var(--line)}
h1+p+h2,h2:first-of-type{border-top:none}
table{font-size:.95em}
@media print{header{position:static}.toc-box{break-inside:avoid}}
"""


PAGES = {
    "backlog": (SOURCE, OUT, TITLE, SUBTITLE),
    "howto": ("docs/HOW-TO-USE-THE-TESTER.md",
              "docs/how-to-use-the-tester.html",
              "How to use the tester — a walkthrough",
              "ISO General Liability Rating Engine · Recursive Harness 2.0 · "
              "run the tests and read the results, no coding"),
    "tomorrow": ("docs/START-HERE-TOMORROW.md",
                 "docs/start-here-tomorrow_20260818.html",
                 "Start here tomorrow — Tuesday 18 August 2026",
                 "ISO General Liability Rating Engine · Recursive Harness 2.0 · "
                 "what to pick up, what is waiting on you, and how far a UI is"),
    "taught": ("docs/WHAT-THE-HARNESS-TAUGHT-US.md",
               "docs/what-the-harness-taught-us_20260817.html",
               "What the harness taught us — 17 August 2026",
               "ISO General Liability Rating Engine · Recursive Harness 2.0 · "
               "seven defects in one day, and the pattern underneath them"),
}


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "backlog"
    if which not in PAGES:
        raise SystemExit(f"unknown page {which!r}; try {', '.join(PAGES)}")
    source, out_rel, title, subtitle = PAGES[which]
    src_path = os.path.join(ROOT, source)
    src = open(src_path, encoding="utf-8").read()

    md = markdown.Markdown(extensions=EXT,
                           extension_configs={"toc": {"toc_depth": "2-2"}})
    body = md.convert(src)
    # ~~strike~~ is not in core python-markdown, same fix build_docs_html makes
    body = re.sub(r"~~(.+?)~~", r"<del>\1</del>", body, flags=re.S)

    meta = (f'Source: <code>{html.escape(source)}</code> &nbsp;·&nbsp; '
            f'{len(src.split()):,} words &nbsp;·&nbsp; rendered '
            f'{datetime.date.today().isoformat()}')

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>{house_css()}{EXTRA}</style></head><body>
<header><h1>{html.escape(title)}</h1>
<div class="sub">{html.escape(subtitle)}</div></header>
<div class="wrap"><article>
<p class="meta">{meta}</p>
<div class="toc-box"><div class="lbl">On this page</div>{md.toc}</div>
{body}
</article></div></body></html>"""

    out = os.path.join(ROOT, out_rel)
    open(out, "w", encoding="utf-8").write(page)
    print(f"wrote {out}  ({os.path.getsize(out) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
