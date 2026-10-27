"""OI-136: corpus files whose Windows path is 260 characters or more are read, not lost.

  A  every rule file, rate / domain / form-page table and data definition in every GL package reads
     through `discovery.read_text` (was: 477 FileNotFoundError on this PC, LongPathsEnabled = 0)
  B  `long_path` is a no-op off Windows and for short paths, and prefixes `\\\\?\\` only when needed
  C  every rule file of the two countrywide parents that had unreadable rules loads through `Program.file`
     (GL_CW_20261001_V01 had 18, GL_CW_20270401_V02 had 14)
  D  a table whose files sit past the limit loads through `load_table` (was: "no table" from `exists()`)

Run: python tests/verify_oi136.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine.erc.discovery import long_path, read_text  # noqa: E402
from gl_engine.erc.tables import load_table  # noqa: E402
from gl_engine.interp.program import Program  # noqa: E402
from gl_engine.resolve.resolver import EditionResolver  # noqa: E402

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(("  ok    " if ok else "  FAIL  ") + label)


R = EditionResolver()
CATS = {"Rules": None, "Rate Tables": "Rate", "Domain Tables": "Domain", "Form Pages": "FormPage", "DataDefs": None}

print("A  every corpus file reads")
n, long_n, bad = 0, 0, []
long_tables = []
for pid, pkg in sorted(R.by_id.items()):
    for cat, kind in CATS.items():
        d = pkg.content / cat
        if not d.is_dir():
            continue
        for f in d.iterdir():
            n += 1
            if len(str(f)) >= 260:
                long_n += 1
                if kind and len(long_tables) < 3 and not any(t[0] == pid for t in long_tables):
                    long_tables.append((pid, pkg, kind, cat, f.name))
            try:
                read_text(f, 10)
            except OSError as exc:
                bad.append(f"{pid} {cat}/{f.name}: {exc}")
check(not bad, f"{n:,} files, {long_n} with paths of 260+ characters, {len(bad)} unreadable")
for b in bad[:5]:
    print("        ", b)

print("B  long_path")
short = Path(r"C:\a\b.xml")
check(long_path(short) == str(short), "a short path is unchanged")
if os.name == "nt":
    lp = Path("C:\\" + "x" * 270 + "\\f.xml")
    got = long_path(lp)
    check(got.startswith("\\\\?\\") and got[4:] == str(PureWindowsPath(lp)), "a long Windows path gets \\\\?\\ once")
    check(long_path(got) == got, "an already-prefixed path is unchanged")

print("C  rule files of the two countrywide parents")
for pid in ("GL_CW_20261001_V01", "GL_CW_20270401_V02"):
    prog = Program(R.by_id[pid])
    names = prog.file_names()
    failed = []
    for name in names:
        try:
            prog.file(name)
        except OSError as exc:
            failed.append(f"{name}: {exc}")
    check(not failed, f"{pid}: {len(names)} of {len(names)} rule files load" if not failed
          else f"{pid}: {len(failed)} rule files fail")

print("D  a table past the limit")
if not long_tables:
    check(True, "no table file in the corpus has a path of 260+ characters (nothing to load)")
for pid, pkg, kind, cat, fname in long_tables:
    for suf in (".RateTableDef.xml", ".RateTable.csv", ".DomainTableDef.xml", ".DomainTable.csv",
                ".FormPageDef.xml", ".FormPage.csv"):
        if fname.endswith(suf):
            name = fname[: -len(suf)]
            name = name[:-3] if name.endswith("Def") else name
            break
    try:
        t = load_table(pkg.content, kind, name, pid)
        check(True, f"{pid} {cat}/{name}: loads")
    except Exception as exc:  # noqa: BLE001
        check(False, f"{pid} {cat}/{name}: {type(exc).__name__}: {exc}")

fails = [label for ok, label in results if not ok]
print(f"\n{'PASS' if not fails else 'FAIL'}: {len(results) - len(fails)} of {len(results)}")
sys.exit(1 if fails else 0)
