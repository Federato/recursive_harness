"""Every rule of a chunk's family files, diffed across the countrywide editions in force.

Carried from chunk 20's gate (2026-09-30): chunk censuses used to diff only `SetPremium` per edition, and
chunk 20's every-rule diff (`203_`) found 6 differences where the SetPremium-only check found 1. Chunk 21
(`211_`, C21-16) ran the every-rule diff and moved it here so each census for chunks 22-27 runs it too.

    import _edition_rules
    _edition_rules.report(lambda name, text: bool(re.search(r"ValueReportingForm", name)))

Editions are the countrywide parents of the 46 in-force states (one line per edition, with its states);
a rule is compared on its text with whitespace, MetadataCodes and ProjectName normalised.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cf_engine.resolve import book_for                                   # noqa: E402

ASOF = "20260917"
_RULE = re.compile(r'<rul:Rule Name="(\w+)".*?</rul:Rule>', re.S)


def _norm(body: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r' MetadataCodes="[^"]*"| ProjectName="[^"]*"', "", body))


def _rules(path: Path) -> dict:
    return {m.group(1): _norm(m.group(0)) for m in _RULE.finditer(path.read_text(encoding="utf-8-sig", errors="replace"))}


def editions(states=None):
    """{edition package name: (content dir, [states])} for the in-force countrywide parents."""
    if states is None:
        from importlib import import_module
        states = import_module("164_chunk14_c14-18_all_states").STATES
    out = {}
    for j in states:
        cw = book_for(j, ASOF).parent.package.content
        out.setdefault(cw.name, (cw, []))[1].append(j)
    return out


def report(select, base_state="OR", states=None, show=40):
    """Print and return every rule difference between the base edition and each other in-force edition, for
    the files `select(file_name, text)` picks in ANY edition. Files present in only some editions are listed."""
    eds = editions(states)
    base = book_for(base_state, ASOF).parent.package.content
    names = set()
    for pkg, _ in eds.values():
        for f in (pkg / "Rules").glob("*.xml"):
            if select(f.name, f.read_text(encoding="utf-8-sig", errors="replace")):
                names.add(f.name)
    diffs = []
    print(f"  every rule of {len(names)} family file(s), four-edition diff against {base.name}:")
    if not names:
        print("    no family file in any countrywide edition (state-only family): nothing to diff")
        return diffs
    for ed, (pkg, js) in sorted(eds.items()):
        if pkg == base:
            print(f"    {ed}: the base ({len(js)} states)")
            continue
        n = 0
        for fn in sorted(names):
            a_path, b_path = base / "Rules" / fn, pkg / "Rules" / fn
            if not a_path.exists() or not b_path.exists():
                diffs.append(f"{ed}: {fn} {'only in ' + ed if not a_path.exists() else 'MISSING'}")
                n += 1
                continue
            a, b = _rules(a_path), _rules(b_path)
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    diffs.append(f"{ed}: {fn.replace('Rules.Rule.xml', '')}.{k} "
                                 f"{'only in the base' if k not in b else 'only here' if k not in a else 'differs'}")
                    n += 1
        print(f"    {ed} ({', '.join(js)}): {n} rule difference(s)")
    for d in diffs[:show]:
        print(f"      {d}")
    if len(diffs) > show:
        print(f"      ... {len(diffs) - show} more")
    return diffs
