"""Extract the Terrorism Supplement into the circular-expert agent's corpus.

The agent shipped with `text/rules` (503) and `text/losscosts` (472) — 975 of the
1,030 documents that were in the manual corpus when it was built. The Terrorism
Supplement (3) and the Schedule & Experience Rating manuals (52) were never
ingested, so every terrorism question the agent was asked had to be answered
from a corpus that did not contain the terrorism rules.

This adds `text/terrorism`. Page markers match the convention the agent's
`pages_of()` splits on, so `iso.py cite` works on these documents unchanged.

Extraction is dual-mode for the reason recorded in `scripts/erc/36_manual_sweep.py`:
this build of `pdftotext` returns zero bytes on a large minority of the corpus
and `pypdf` reads those files in full. `-layout` is used first because the
Supplement's class-code table is two-columned.

    python scripts/13_extract_terrorism.py
"""
from __future__ import annotations

import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SRC = os.path.join(PROJ, "Commercial Line Manuals", "GL", "Terrorism")
DST = os.path.join(PROJ, "Agentic", "iso-circular-expert", "text", "terrorism")


def page_texts(path: str) -> list[str]:
    """Per-page text, pdftotext first, pypdf where it comes back empty."""
    pages: list[str] = []
    try:
        n = int(subprocess.run(["pdfinfo", path], capture_output=True
                               ).stdout.decode("utf-8", "replace")
                .split("Pages:")[1].split()[0])
    except Exception:                                           # noqa: BLE001
        n = 0
    if n:
        for i in range(1, n + 1):
            r = subprocess.run(["pdftotext", "-q", "-layout", "-f", str(i),
                                "-l", str(i), path, "-"], capture_output=True)
            pages.append(r.stdout.decode("utf-8", "replace"))
    if not any(p.strip() for p in pages):
        import warnings

        import pypdf
        warnings.filterwarnings("ignore")
        rd = pypdf.PdfReader(path, strict=False)
        pages = [(p.extract_text() or "") for p in rd.pages]
    return pages


def main() -> int:
    os.makedirs(DST, exist_ok=True)
    pdfs = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".pdf"))
    print(f"population: {len(pdfs)} terrorism documents in {SRC}")
    for f in pdfs:
        pages = page_texts(os.path.join(SRC, f))
        body = "".join(f"\n<<<PAGE {i + 1}>>>\n" + t
                       for i, t in enumerate(pages))
        out = os.path.join(DST, f[:-4] + ".txt")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"  {f}: {len(pages)} pages, {len(body):,} chars -> "
              f"{os.path.relpath(out, PROJ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
