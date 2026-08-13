"""Ingest a manual family into the circular-expert agent's text corpus.

Generalises `13_extract_terrorism.py`, which was written for one folder and then
immediately needed for two more. The agent shipped with `Rules` and `LossCosts`
only; **the Terrorism Supplement, the Schedule & Experience Rating manuals and
the Composite Rating manuals were all on disk and none was ingested** (OI-55), so
every question about them was answered from a corpus that did not contain them.

    python scripts/15_extract_manual_family.py "Schedule & Experience Rating" scheduleexperience
    python scripts/15_extract_manual_family.py "Composite Rating" compositerating
    python scripts/15_extract_manual_family.py --all

Page markers match the convention `iso.py pages_of()` splits on, so `cite` and
`page` work on these documents unchanged.

Extraction is dual-mode — `pdftotext -layout` first, `pypdf` where that returns
under 200 characters. That is not an optimisation: this build of `pdftotext`
returns **zero bytes** on a large minority of the corpus, and a single-mode sweep
reported 187 documents as image-only when none of them was (OI-51, withdrawn).
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
MANUALS = os.path.join(PROJ, "Commercial Line Manuals", "GL")
TEXT = os.path.join(PROJ, "Agentic", "iso-circular-expert", "text")

FAMILIES = [
    ("Terrorism", "terrorism"),
    ("Schedule & Experience Rating", "scheduleexperience"),
    ("Composite Rating", "compositerating"),
]


def page_texts(path: str) -> list[str]:
    pages: list[str] = []
    try:
        info = subprocess.run(["pdfinfo", path], capture_output=True
                              ).stdout.decode("utf-8", "replace")
        n = int(info.split("Pages:")[1].split()[0])
    except Exception:                                           # noqa: BLE001
        n = 0
    if n:
        for i in range(1, n + 1):
            r = subprocess.run(["pdftotext", "-q", "-layout", "-f", str(i),
                                "-l", str(i), path, "-"], capture_output=True)
            pages.append(r.stdout.decode("utf-8", "replace"))
    if sum(len(p.strip()) for p in pages) < 200:
        try:
            import warnings

            import pypdf
            warnings.filterwarnings("ignore")
            pages = [(p.extract_text() or "")
                     for p in pypdf.PdfReader(path, strict=False).pages]
        except Exception as e:                                  # noqa: BLE001
            print(f"      ! both extractors failed: {type(e).__name__}")
            return []
    return pages


def ingest(folder: str, slug: str) -> tuple[int, int, list[str]]:
    src = os.path.join(MANUALS, folder)
    dst = os.path.join(TEXT, slug)
    os.makedirs(dst, exist_ok=True)
    pdfs = sorted(f for f in os.listdir(src) if f.lower().endswith(".pdf"))
    print(f"\n{folder} -> text/{slug}/   population: {len(pdfs)} documents")
    ok = 0
    pages_tot = 0
    empty: list[str] = []
    for f in pdfs:
        pages = page_texts(os.path.join(src, f))
        if not pages or not any(p.strip() for p in pages):
            empty.append(f)
            continue
        body = "".join(f"\n<<<PAGE {i + 1}>>>\n" + t for i, t in enumerate(pages))
        with open(os.path.join(dst, f[:-4] + ".txt"), "w", encoding="utf-8") as fh:
            fh.write(body)
        ok += 1
        pages_tot += len(pages)
    print(f"  {ok} of {len(pdfs)} extracted · {pages_tot:,} pages"
          + (f" · UNREADABLE {empty}" if empty else ""))
    return ok, len(pdfs), empty


def main() -> int:
    args = sys.argv[1:]
    if args == ["--all"]:
        jobs = FAMILIES
    elif len(args) == 2:
        jobs = [(args[0], args[1])]
    else:
        print(__doc__)
        return 2
    grand = 0
    for folder, slug in jobs:
        ok, n, _empty = ingest(folder, slug)
        grand += ok
    print(f"\n{grand} documents now in the agent corpus from this run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
