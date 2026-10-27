"""Ingest the CF (Commercial Property) manual corpus into cf-circular-expert's text corpus.

Mirrors `15_extract_manual_family.py`'s approach for GL. Started 2026-08-19 with six countrywide
Rules notices at `Commercial Line Manuals\\CF\\CW\\`. State-specific folders (`AK`, `AL`, `AR`,
`AZ`, `CA`, ...) were added the same day — this script now sweeps **every subfolder** of
`Commercial Line Manuals\\CF\\`, not just `CW`, and re-run after more states land; it re-extracts
everything each run rather than tracking incremental state, matching the GL scripts' behavior.

    python scripts/16_extract_cf_manuals.py

Page markers use the same `<<<PAGE n>>>` convention as the GL corpus, so any future
`cf-manual.py` CLI can reuse GL's `pages_of()` / `cite()` / `page()` implementations
unchanged. Output text files are written flat into `text/rules/` (not one subfolder per state) —
the filename's own state code (`CF-<ST>-...`) is the partition, matching how the GL corpus
distinguishes documents within one flat `text/rules/` folder.

Extraction is dual-mode — `pdftotext -layout` first, `pypdf` where that returns under 200
characters — same rationale as the GL extractor: a single-mode sweep undercounts readable
documents. This machine has no `pdfinfo` on PATH (confirmed 2026-08-19), so the `pdfinfo`
page-count step always falls through to the `pypdf` fallback path here; that is expected,
not a failure, and is logged per-document below.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SRC_ROOT = os.path.join(PROJ, "Commercial Line Manuals", "CF")
DST = os.path.join(PROJ, "Agentic", "cf-circular-expert", "text", "rules")
KNOWLEDGE_DIR = os.path.join(PROJ, "Agentic", "cf-circular-expert", "knowledge")


def page_texts(path: str) -> tuple[list[str], str]:
    """Returns (pages, method) where method is 'pdftotext' or 'pypdf'."""
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
            return pages, "pypdf"
        except Exception as e:                                  # noqa: BLE001
            print(f"      ! both extractors failed: {type(e).__name__}")
            return [], "none"
    return pages, "pdftotext"


def main() -> int:
    if not os.path.isdir(SRC_ROOT):
        print(f"Source root not found: {SRC_ROOT}")
        return 2
    os.makedirs(DST, exist_ok=True)
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

    state_dirs = sorted(d for d in os.listdir(SRC_ROOT)
                         if os.path.isdir(os.path.join(SRC_ROOT, d)))
    print(f"CF/ -> text/rules/   state folders found: {state_dirs}")

    registry = {"rules": {}}
    ok = 0
    total_pdfs = 0
    pages_tot = 0
    empty: list[str] = []

    for state_dir in state_dirs:
        src = os.path.join(SRC_ROOT, state_dir)
        pdfs = sorted(f for f in os.listdir(src) if f.lower().endswith(".pdf"))
        total_pdfs += len(pdfs)
        print(f"\n{state_dir}/  population: {len(pdfs)} documents")

        for f in pdfs:
            path = os.path.join(src, f)
            pages, method = page_texts(path)
            if not pages or not any(p.strip() for p in pages):
                empty.append(f)
                print(f"  ! {f}: UNREADABLE")
                continue

            body = "".join(f"\n<<<PAGE {i + 1}>>>\n" + t for i, t in enumerate(pages))
            out_name = f[:-4] + ".txt"
            with open(os.path.join(DST, out_name), "w", encoding="utf-8") as fh:
                fh.write(body)

            # Filename convention observed: CF-<ST>-<year>-RU-<seq>-C.pdf (MU = countrywide)
            parts = f[:-4].split("-")
            st = parts[1] if len(parts) > 1 else state_dir
            edition_year = parts[2] if len(parts) > 2 else None
            seq = parts[4] if len(parts) > 4 else None

            registry["rules"][f] = {
                "file": f,
                "kind": "RU",
                "st": st,
                "source_folder": state_dir,
                "notice": f[:-6] if f.endswith("-C.pdf") else f[:-4],
                "pages": len(pages),
                "edition_year": edition_year,
                "seq": seq,
                "extraction_method": method,
                "state_specific": st != "MU",
                "circulars": [],
                "filings": [],
                "effective_date": None,
                "date_confidence": "Unverified — not yet cross-checked against a circular or ERC edition",
            }

            ok += 1
            pages_tot += len(pages)
            print(f"  {f}: {len(pages)} pages ({method})")

    print(f"\n{ok} of {total_pdfs} extracted, {pages_tot:,} pages total"
          + (f"; UNREADABLE: {empty}" if empty else ""))

    registry_path = os.path.join(KNOWLEDGE_DIR, "notices.json")
    with open(registry_path, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=1)
    print(f"Wrote {registry_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
