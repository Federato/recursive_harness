"""Rule #1, applied: every directory in an ISO package, and what it is for.

**Designated the project's first rule on 2026-08-13**, after the third time an
answer turned out to be filed in a directory nobody had opened -- the `Default`
block, the response header naming the edition, and the submission schema.

This enumerates **every** directory and file type across the corpus, including
the ones no part of this build has ever read, and reports what each contains.
The point is the ones at the bottom of the list: a directory whose purpose is
unknown is an unmeasured population.

  D1 categories   every directory name that appears, in how many packages
  D2 shapes       the file types inside each, and how many
  D3 used         which the engine actually reads today, and which it does not
  D4 unknown      the ones with no stated purpose -- the reason this exists
  D5 sample       for each unread directory, one file's header or root element,
                  so "what is it for" is answered rather than deferred

Emits out/directory_census.txt.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

#: What the engine reads today, and where. Anything not here is unread, and
#: saying so is the whole point of this script.
READ_BY_ENGINE = {
    "DataDefs": "stage 1 -- package identity and declared parent, from the "
                "XSD targetNamespace (N6, N5)",
    "Rate Tables": "stages 1-3 -- rates, factors, loss costs; banded and "
                   "interpolated lookups",
    "Domain Tables": "stages 3-4 -- legal values for a field (DataValue)",
    "Rules": "stage 2 -- the rule language; the Default block is the entry "
             "point",
    "Form Fields": "stage 4 -- the submission schema ISO files",
    "Ratebook Columns": "stage 4 -- RatingRequiredCondition, required to rate",
    "Form Pages": "stage 2 -- the `Pages` table, the most common Lookup target",
}


def sample_file(d: Path) -> str:
    """One line describing what is actually inside."""
    files = sorted(p for p in d.iterdir() if p.is_file())
    if not files:
        return "(empty)"
    f = files[0]
    try:
        if f.suffix.lower() == ".csv":
            head, _ = c.read_csv_rows(f)
            return f"{f.name}: columns {head[:8]}"
        text = c.read_text(f)[:400].strip()
        if text.startswith("<"):
            root = text.split(">", 1)[0].lstrip("<").split()[0]
            return f"{f.name}: XML root <{root}>"
        return f"{f.name}: {text[:90]!r}"
    except Exception as exc:                              # noqa: BLE001
        return f"{f.name}: ({type(exc).__name__})"


def main() -> None:
    pkgs, n_dirs, _ = rules_packages()

    cats = Counter()
    suffixes = defaultdict(Counter)
    counts = defaultdict(list)
    samples = {}

    for pk in pkgs:
        for d in sorted(p for p in pk.content.iterdir() if p.is_dir()):
            cats[d.name] += 1
            n = 0
            for f in d.iterdir():
                if f.is_file():
                    n += 1
                    suffixes[d.name][
                        "".join(f.suffixes[-2:]) or f.suffix or "(none)"] += 1
            counts[d.name].append(n)
            if d.name not in samples and n:
                samples[d.name] = sample_file(d)

    L = []; A = L.append
    A("EVERY DIRECTORY IN AN ISO PACKAGE, AND WHAT IT IS FOR")
    A("")
    A("Rule #1, applied. Written because three times in this build the answer")
    A("was already filed in a directory nobody had opened.")
    A("")
    A(f"    packages: {len(pkgs)}")
    A(f"    distinct directory names: {len(cats)}")
    A("")
    A("D1/D2  CATEGORIES, PRESENCE AND CONTENT")
    A(f"    {'directory':24s} {'pkgs':>5s} {'files: min..max':>16s}  file types")
    for name, n in cats.most_common():
        v = sorted(counts[name])
        types = ", ".join(f"{k}({m})" for k, m in
                          suffixes[name].most_common(3))
        A(f"    {name:24s} {n:5d} {v[0]:7d}..{v[-1]:<7d} {types}")
    A("")
    A("D3  READ BY THE ENGINE TODAY")
    for name in sorted(cats):
        if name in READ_BY_ENGINE:
            A(f"    {name:24s} {READ_BY_ENGINE[name]}")
    A("")
    A("D4  NOT READ BY THE ENGINE  -- the reason this script exists")
    unread = [n for n in sorted(cats) if n not in READ_BY_ENGINE]
    A(f"    {len(unread)} of {len(cats)} directories are never opened by the "
      f"engine:")
    for name in unread:
        A(f"      {name:24s} in {cats[name]} packages, "
          f"{sorted(counts[name])[-1]} files at most")
    A("")
    A("D5  WHAT IS ACTUALLY IN THE UNREAD ONES")
    for name in unread:
        A(f"    {name}")
        A(f"      {samples.get(name, '(no sample)')}")

    (c.OUT / "directory_census.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
