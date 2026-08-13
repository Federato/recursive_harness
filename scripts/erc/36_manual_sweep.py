"""Enumerate the ENTIRE manual corpus and classify every document for a phrase.

Habit 8, applied to a negative claim. Gate item 8 needs to say whether the ISO
manual anywhere describes size-of-risk rating. "I searched the multistate rules
manual and found nothing" is exactly the shape of claim this project keeps
getting wrong: the denominator came from the query. So the population is EVERY
pdf under `Commercial Line Manuals/`, and every one is opened and classified.

Text extraction is `pdftotext` (poppler) across a process pool — pypdf took
~7 s/document, which put a full sweep at two hours and would have pushed this
check into the "too slow to actually run" category where negative claims get
made from a subset instead.

    python 36_manual_sweep.py                       # size-of-risk
    python 36_manual_sweep.py "experience rat"      # any regex

Prints "n of N" plus the documents that could NOT be read, which are part of the
denominator too: a document that failed to parse is not evidence of absence.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "Commercial Line Manuals")
DEFAULT = r"size[\s\-]*of[\s\-]*risk"


def scan(job: tuple[str, str]) -> tuple[str, int, int, str]:
    """-> (path, n_matches, n_chars, error).

    DUAL-MODE, and that is not an optimisation — it is the difference between a
    true and a false claim. The first version of this script used `pdftotext`
    alone and reported **187 of 1,030 documents have no text layer**, which was
    then written into a gate as a bound on a negative claim. It is wrong: this
    build of `pdftotext` returns zero bytes on those files, and `pypdf` extracts
    them in full (`GL-CT-2026-LC-001-C`: 0 bytes vs 218,978). The project's own
    `scripts/02_extract_dualmode_losscosts.py` already had the fallback; this
    script did not, and nothing compared them.

    So: `pdftotext` first because it is ~40x faster, `pypdf` whenever that
    yields under 200 characters. `n_chars == 0` now means BOTH extractors failed,
    which is a much smaller and much more honest class.
    """
    path, pattern = job
    txt = ""
    try:
        r = subprocess.run(["pdftotext", "-q", path, "-"],
                           capture_output=True, timeout=300)
        txt = r.stdout.decode("utf-8", "replace")
    except Exception:                                           # noqa: BLE001
        txt = ""
    if len(txt.strip()) < 200:
        try:
            import warnings

            import pypdf
            warnings.filterwarnings("ignore")
            rd = pypdf.PdfReader(path, strict=False)
            txt = "\n".join((p.extract_text() or "") for p in rd.pages)
        except Exception as e:                                  # noqa: BLE001
            return path, 0, 0, f"{type(e).__name__}: {e}"
    return path, len(re.findall(pattern, txt, re.I)), len(txt), ""


def main() -> int:
    pattern = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    pdfs = sorted(os.path.join(dp, fn)
                  for dp, _dn, fns in os.walk(BASE)
                  for fn in fns if fn.lower().endswith(".pdf"))
    print(f"population: {len(pdfs)} pdf documents under {BASE}")
    print(f"pattern:    {pattern}\n", flush=True)

    hits: list[tuple[str, int]] = []
    empty: list[str] = []
    errs: list[str] = []
    done = 0
    with ProcessPoolExecutor() as ex:
        for path, n, chars, err in ex.map(scan, ((p, pattern) for p in pdfs)):
            done += 1
            rel = os.path.relpath(path, BASE)
            if err:
                errs.append(f"{rel} — {err}")
            elif not chars:
                empty.append(rel)
            elif n:
                hits.append((rel, n))
            if done % 200 == 0:
                print(f"  ...{done} of {len(pdfs)} read, {len(hits)} hits",
                      flush=True)

    readable = len(pdfs) - len(errs) - len(empty)
    print(f"\n{len(hits)} of {len(pdfs)} documents match "
          f"({readable} carried a text layer, {len(empty)} had none, "
          f"{len(errs)} failed to read)")

    # Where the un-searchable documents sit matters as much as how many there
    # are: 187 image-only files concentrated in one family bounds the residual
    # to that family, which a bare count cannot say.
    def fam(rel: str) -> str:
        parts = rel.split(os.sep)
        return parts[1] if len(parts) > 1 else parts[0]

    tot: dict[str, int] = {}
    notext: dict[str, int] = {}
    for p in pdfs:
        tot[fam(os.path.relpath(p, BASE))] = \
            tot.get(fam(os.path.relpath(p, BASE)), 0) + 1
    for rel in empty:
        notext[fam(rel)] = notext.get(fam(rel), 0) + 1
    print("\nby manual family — documents with no text layer:")
    for f in sorted(tot):
        print(f"  {f:<32} {notext.get(f, 0):>3} of {tot[f]:>4}")
    for rel, n in hits:
        print(f"  {n:>4}x  {rel}")
    for label, xs in (("NO TEXT LAYER — not evidence of absence", empty),
                      ("FAILED TO READ — not evidence of absence", errs)):
        if xs:
            print(f"\n{label} ({len(xs)}):")
            for x in xs[:40]:
                print(f"  {x}")
            if len(xs) > 40:
                print(f"  … and {len(xs) - 40} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
