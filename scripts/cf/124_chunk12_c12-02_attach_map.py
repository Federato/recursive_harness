#!/usr/bin/env python3
"""Chunk 12, C12-02 -- the attach map, read from the rules, not inferred.

For every datadef group the six endorsement families own, this answers four
questions from the filed XML itself:

  1  WHO DRIVES IT -- which record's `ErcProcess` / `CalculateTotalPremium`
     `ForEach`es over the family's table. A record nobody iterates is never
     rated, whatever the payload says.
  2  WHO CREATES IT -- every `Locate ... OutputAction="Append"` aimed at the
     table, and the gate it sits behind. A created record is rated whether
     or not the submitter sent it.
  3  WHO DELETES IT -- every `Remove` aimed at the table, and the gate it
     sits behind. Chunk 11's lesson: the Structure's attach rule silently
     deleted a submitted Leasehold Interest record because `CovType` was
     not `Leasehold Interest`. C10-17's: a record hangs off a parent you
     would not guess from its name.
  4  WHO CHANGES THAT BY STATE -- every one of the 46 state layers (Puerto
     Rico excluded) checked for an override of each rule found in 2 and 3.

The gates are rendered as short expressions so the map can be read, then the
full map is written to `docs/CF-CHUNK12-ATTACH-MAP.md`.

    python scripts/cf/124_chunk12_c12-02_attach_map.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import collections
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for

census = import_module("123_chunk12_census")
census11 = import_module("106_chunk11_census")
ASOF = census.ASOF
NS = "{http://www.verisk.com/iso/erc/Rule}"
OUT = Path(__file__).resolve().parents[2] / "docs" / "CF-CHUNK12-ATTACH-MAP.md"
CORE = "CommercialProperty"


def tag(el):
    return el.tag.replace(NS, "")


def short(path: str) -> str:
    """`...Table/CommercialPropertyFoo[1]/Bar` -> `Foo/Bar`."""
    segs = [s for s in path.split("/") if s and not s.endswith("Table")]
    return "/".join(re.sub(r"^CommercialProperty", "", s) for s in segs) or path


def render(el) -> str:
    """A gate as a short expression. Good enough to read, not to evaluate."""
    t, a, kids = tag(el), el.attrib, list(el)
    if t in ("Test", "Sequence") and len(kids) == 1:
        return render(kids[0])
    if t in ("And", "Or"):
        return "(" + f" {t.upper()} ".join(render(k) for k in kids) + ")"
    ops = {"Equal": "=", "NotEqual": "!=", "GreaterThan": ">", "LessThan": "<",
           "GreaterThanOrEqual": ">=", "LessThanOrEqual": "<="}
    if t in ops and len(kids) == 2:
        return f"{render(kids[0])} {ops[t]} {render(kids[1])}"
    if t == "Constant":
        return repr(el.text or "")
    if t in ("FirstValue", "Value"):
        src = a.get("FromDataDef") or ("$" + a.get("FromParam", "?"))
        dflt = a.get("FromConstant")
        return short(src) + (f"[or {dflt!r}]" if dflt not in (None, "") else "")
    if t in ("Exist", "NotExist"):
        return f"{t}({short(a.get('AtInputDataDef', '?'))})"
    if t in ("IsNull", "IsNotNull"):
        return f"{t}({render(kids[0]) if kids else '?'})"
    if t == "RunRule":
        return f"{a.get('Rule')}()"
    if t == "Count":
        return f"Count({short(a.get('AtInputDataDef', '?'))})"
    return f"{t}(" + ", ".join(render(k) for k in kids) + ")"


def gate_of(el, parents) -> str:
    """Every enclosing If / When between `el` and its rule, outermost first."""
    bits, cur = [], el
    while cur in parents:
        par = parents[cur]
        pt = tag(par)
        if pt in ("Then", "Else"):
            iff = parents[par]
            test = next((k for k in iff if tag(k) == "Test"), None)
            cond = render(test) if test is not None else "?"
            bits.append(cond if pt == "Then" else f"NOT[{cond}]")
        elif pt == "When":
            test = next((k for k in par if tag(k) == "Test"), None)
            if test is not None and test is not cur:
                bits.append(render(test))
        elif pt == "Otherwise":
            bits.append("OTHERWISE(no When matched)")
        elif pt == "Rule":
            break
        cur = par
    return " AND ".join(reversed(bits)) or "(always)"


def rule_of(el, parents):
    cur = el
    while cur in parents:
        cur = parents[cur]
        if tag(cur) == "Rule":
            return cur
    return None


def family_groups(all_rules):
    """{group: (family, file)} for every family file's own DataDefGroup."""
    out = {}
    for fam, key in census.FAMILIES.items():
        for n, s in all_rules.items():
            if key not in n:
                continue
            m = re.search(r'<rul:Rule Name="[^"]+"[^>]*DataDefGroup="([^"]+)"', s)
            if m:
                out[m.group(1)] = (fam, n)
    return out


def scan(texts, groups):
    """Every drive / run / create / delete aimed at a family group."""
    pat = re.compile("|".join(sorted(map(re.escape, groups), key=len, reverse=True)))
    hits = []            # (group, kind, file, rule, gate, extra)
    for fname, s in texts.items():
        if not pat.search(s):
            continue
        root = ET.fromstring(s)
        parents = {c: p for p in root.iter() for c in p}
        for el in root.iter():
            t = tag(el)
            if t in ("ForEach", "Remove"):
                path = el.attrib.get("AtDataDef")
            elif t == "Locate":
                path = (el.attrib.get("AtOutputDataDef") or el.attrib.get("AtInputDataDef")
                        or el.attrib.get("AtDataDef"))
            else:
                continue
            if not path:
                continue
            last = [x for x in re.sub(r"\[\d+\]", "", path).split("/") if x][-1]
            if last not in groups:
                continue
            if t == "Locate":
                if "AtOutputDataDef" in el.attrib:
                    if el.attrib.get("OutputAction") != "Append":
                        continue
                    kind = "creates"
                else:
                    runs = {rr.attrib.get("Rule") for rr in el.iter(NS + "RunRule")}
                    if not runs & {"ErcProcess", "CalculateTotalPremium"}:
                        continue
                    kind = "drives"
            else:
                kind = {"ForEach": "drives", "Remove": "deletes"}[t]
            r = rule_of(el, parents)
            rname = r.attrib.get("Name") if r is not None else "?"
            if kind == "drives":
                runs = {rr.attrib.get("Rule") for rr in el.iter(NS + "RunRule")}
                if not runs & {"ErcProcess", "CalculateTotalPremium"}:
                    continue            # InitializeRuleSet-only loops set up, they do not rate
            hits.append((last, kind, fname, rname, gate_of(el, parents),
                         el.attrib.get("RemoveMultiple", "")))
    return hits


def main():
    b = book_for("OR", ASOF)
    rules_dir = b.parent.package.content / "Rules"
    texts = {f.name: f.read_text(encoding="utf-8-sig") for f in rules_dir.glob("*.xml")}
    groups = family_groups(texts)
    print(f"{b}\n{len(groups)} family datadef groups across "
          f"{len({f for _, f in groups.values()})} files\n")

    hits = scan(texts, groups)

    # A state layer can ADD a create/delete the countrywide package does not
    # have -- an overlay carries only its adds, so scan every state's own
    # rule files the same way and keep what CW lacks.
    # State overrides of every create/delete rule.
    books = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            books[j] = book_for(j, ASOF)
        except Exception:
            pass
    cw_keys = {(g, k, f, r) for g, k, f, r, _, _ in hits}
    state_adds = collections.defaultdict(list)       # (g, k, f, r, gate) -> [states]
    state_only = collections.defaultdict(list)       # group -> [(state, file, rates?)]
    for j, bk in books.items():
        sdir = bk.state.package.content / "Rules"
        if not sdir.exists():
            continue
        stexts = {f.name: f.read_text(encoding="utf-8-sig") for f in sdir.glob("*.xml")}
        # A state can file a family group the countrywide package does not
        # have at all (VA's broad form, WV's Flood cells). Scan for those too.
        sgroups = dict(groups)
        for g, (fam, fn) in family_groups(stexts).items():
            if g not in groups:
                sgroups[g] = (fam, fn)
                state_only[g].append((j, fn, '"SetPremium"' in stexts[fn]))
        for g, k, f, r, gt, _ in scan(stexts, sgroups):
            if (g, k, f, r) not in cw_keys and k in ("creates", "deletes", "drives"):
                state_adds[(g, k, f, r, gt)].append(j)
    need = {(f, r) for _, k, f, r, _, _ in hits if k in ("creates", "deletes")}
    overrides = collections.defaultdict(list)       # (file, rule) -> [(state, same?)]
    pins = collections.defaultdict(list)            # (file, rule) -> [states]
    cw_body = {}
    for f, r in need:
        m = re.search(rf'<rul:Rule Name="{re.escape(r)}"[\s\S]*?</rul:Rule>', texts[f])
        cw_body[(f, r)] = re.sub(r"\s+", "", m.group(0)) if m else ""
    for j, bk in books.items():
        sdir = bk.state.package.content / "Rules"
        for f, r in need:
            p = sdir / f
            if not p.exists():
                continue
            st = p.read_text(encoding="utf-8-sig")
            m = re.search(rf'<rul:Rule Name="{re.escape(r)}"[\s\S]*?</rul:Rule>', st)
            if m:
                body = re.sub(r"\s+", "", m.group(0))
                pin = re.fullmatch(r'<rul:Rule[^>]*><rul:Sequence><rul:RunRule[^>]*'
                                   r'ProjectName="([^"]+)"[^>]*/></rul:Sequence></rul:Rule>', body)
                parent = bk.parent.package.content.name.replace(" ", "").upper()
                if pin and pin.group(1).replace(" ", "").upper() == parent:
                    pins[(f, r)].append(j)          # "run my declared parent's copy"
                else:
                    overrides[(f, r)].append((j, body == cw_body[(f, r)]))

    # Report, family by family.
    by_group = collections.defaultdict(list)
    for h in hits:
        by_group[h[0]].append(h)
    lines = []
    summary = []
    for fam in census.FAMILIES:
        gs = sorted(g for g, (f, _) in groups.items() if f == fam)
        top = [g for g in gs if any(fn.startswith(CORE) and groups.get(
            _group_of(texts[fn]), (None,))[0] != fam
            for _, _, fn, _, _, _ in by_group[g])]
        lines.append(f"\n## {fam}\n")
        lines.append(f"{len(gs)} datadef groups; {len(top)} hang directly off a core "
                     f"(non-family) record, the rest are children of the family's own records.\n")
        lines.append("| Group | Parent record (file) | Driven by | Created when | Deleted when | State overrides of create/delete |")
        lines.append("|---|---|---|---|---|---|")
        for g in gs:
            hs = by_group[g]
            parents_ = sorted({_group_of(texts[fn]) for _, _, fn, _, _, _ in hs})
            drives = sorted({f"`{r}`" + ("" if gt == "(always)" else f": {gt}")
                             for _, k, _, r, gt, _ in hs if k == "drives"})
            creates = sorted({f"`{r}`: {gt}" for _, k, _, r, gt, _ in hs if k == "creates"})
            deletes = sorted({f"`{r}`: {gt}" for _, k, _, r, gt, _ in hs if k == "deletes"})
            ov = []
            for _, k, f, r, _, _ in hs:
                if k in ("creates", "deletes") and pins.get((f, r)):
                    ov.append(f"`{r}` pinned to parent in {len(pins[(f, r)])} states")
                if k in ("creates", "deletes") and overrides.get((f, r)):
                    diff = [s for s, same in overrides[(f, r)] if not same]
                    ov.append(f"`{r}` in {len(overrides[(f, r)])} states"
                              + (f", DIFFERENT in {','.join(diff)}" if diff else ", all identical"))
            row = (short(g), ", ".join(short(p) for p in parents_) or "**none**",
                   ", ".join(drives) or "**nobody**",
                   "<br>".join(creates) or "not auto-created (submitted only)",
                   "<br>".join(deletes) or "never",
                   "<br>".join(sorted(set(ov))) or "none")
            lines.append("| " + " | ".join(x.replace("|", "\\|") for x in row) + " |")
            summary.append((fam, g, parents_, bool(drives), bool(creates), bool(deletes),
                            sorted(set(ov))))

    # Console summary.
    print(f"{'family':22s} {'groups':>6s} {'orphans':>7s} {'auto-created':>12s} "
          f"{'deletable':>9s} {'state-changed':>13s}")
    for fam in census.FAMILIES:
        rows = [s for s in summary if s[0] == fam]
        print(f"{fam:22s} {len(rows):6d} {sum(not s[3] for s in rows):7d} "
              f"{sum(s[4] for s in rows):12d} {sum(s[5] for s in rows):9d} "
              f"{sum(any('DIFFERENT' in o for o in s[6]) for s in rows):13d}")
    print("\nTop-level records (parent is a core group): who drives them, under what gate")
    for fam, g, ps, d, c, dl, ov in summary:
        core_ps = [p for p in ps if groups.get(p, (None,))[0] != fam]
        if not core_ps:
            continue
        print(f"  [{fam}] {short(g)}  <- {', '.join(short(p) for p in core_ps)}")
        for k in ("drives", "creates", "deletes"):
            for gt in sorted({gt for gg, kk, _, r, gt, _ in hits if gg == g and kk == k}):
                print(f"        {k}: {gt[:200]}")
    print("\nChild records: the distinct gates they are CREATED behind, per family")
    for fam in census.FAMILIES:
        gates = collections.Counter(
            re.sub(r"(Coverage|Cov)\w*", r"\1*", gt)
            for g, k, _, _, gt, _ in hits if k == "creates" and groups[g][0] == fam)
        print(f"  [{fam}] {sum(gates.values())} creates, {len(gates)} distinct gate shapes")
        for gt, n in gates.most_common(8):
            print(f"      {n:3d}x  {gt[:190]}")
    print("\nState overrides of a CW create rule that DIFFER from CW:")
    diffs = sorted({(f, r, tuple(s_ for s_, same in v if not same))
                    for (f, r), v in overrides.items() if any(not same for _, same in v)})
    for f, r, sts in diffs:
        print(f"  {f.replace('CommercialProperty', '').replace('Rules.Rule.xml', '')}::{r}  "
              f"{','.join(sts)}")
    print(f"  ({len(diffs)} rules)")
    print("\nDrives / creates / deletes a STATE adds that CW does not have:")
    for (g, k, f, r, gt), sts in sorted(state_adds.items()):
        print(f"  {k:8s} {short(g)} in {f.replace('Rules.Rule.xml', '')}::{r} "
              f"[{','.join(sts)}]: {gt[:150]}")
    print(f"  ({len(state_adds)} found)")
    print(f"\nFamily groups that exist ONLY in a state layer: {len(state_only)}")
    for g, v in sorted(state_only.items()):
        driven = sorted({(k, r) for (gg, k, f, r, gt) in state_adds if gg == g})
        print(f"  {short(g)} {[x[0] for x in v]} rates={v[0][2]}  <- "
              f"{', '.join(f'{k}:{r}' for k, r in driven) or 'NOBODY DRIVES IT'}")

    # The parent editions themselves: 9 states sit on an older CW.
    by_parent = collections.defaultdict(list)
    for j, bk in books.items():
        by_parent[bk.parent.package.content].append(j)
    base = {(g, k, r, gt) for g, k, _, r, gt, _ in hits}
    print(f"\nParent editions ({len(by_parent)}): same create/drive/delete map as "
          f"{b.parent.package.content.name}?")
    lines.append("\n## Parent editions\n")
    for pdir, sts in sorted(by_parent.items(), key=lambda x: x[0].name):
        ptexts = {f.name: f.read_text(encoding="utf-8-sig") for f in (pdir / "Rules").glob("*.xml")}
        ph = {(g, k, r, gt) for g, k, _, r, gt, _ in scan(ptexts, family_groups(ptexts))}
        verdict = "identical" if ph == base else f"{len(ph ^ base)} differences"
        print(f"  {pdir.name:22s} {len(sts):2d} states: {verdict}")
        lines.append(f"* `{pdir.name}` ({', '.join(sorted(sts))}): {verdict}")
    npins = sum(len(v) for v in pins.values())
    print(f"\nState overrides that only pin to the declared parent: {npins} "
          f"across {len(pins)} rules (content = that parent's rule)")
    lines.append(f"\n{npins} state overrides of a create rule, across {len(pins)} rules, are "
                 f"pure pins: the whole body is one `RunRule` with `ProjectName` equal to the "
                 f"state's declared parent. The engine sends every `ProjectName` call to the "
                 f"declared parent, so these resolve to the parent editions above.\n")
    lines.append("\n## State layer\n")
    lines.append("CW create/delete rules a state overrides with a DIFFERENT body:\n")
    for f, r, sts in diffs:
        lines.append(f"* `{f}` :: `{r}` -- {', '.join(sts)}")
    lines.append(f"\nDrives, creates or deletes a state adds that CW lacks: {len(state_adds)}\n")
    for (g, k, f, r, gt), sts in sorted(state_adds.items()):
        lines.append(f"* {k} `{short(g)}` in `{f}` :: `{r}` [{', '.join(sts)}]: {gt}")
    lines.append(f"\nFamily groups filed ONLY by a state (absent from every countrywide "
                 f"edition): {len(state_only)}\n")
    for g, v in sorted(state_only.items()):
        lines.append(f"* `{short(g)}` -- {', '.join(x[0] for x in v)}"
                     f"{'' if v[0][2] else ' (no SetPremium)'}")

    OUT.write_text(
        "# Chunk 12, C12-02: the attach map\n\n"
        f"Generated by `scripts/cf/124_chunk12_c12-02_attach_map.py` against "
        f"`{b.parent.package.content.name}` (as of {ASOF}). Do not hand-edit; re-run.\n\n"
        "Each row is one datadef group a family owns. **Driven by** is the rule in the "
        "parent that `ForEach`es over it (a record nobody drives is never rated). "
        "**Created when** is an `OutputAction=\"Append\"` `Locate`: the record exists "
        "whether or not it was submitted. **Deleted when** is a `Remove`: a submitted "
        "record is silently dropped. Gates are the enclosing `If`/`When` tests, outermost "
        "first; `NOT[...]` means the action sits in the `Else`.\n"
        + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(OUT.parents[1])}")
    return 0


def _group_of(text: str) -> str:
    m = re.search(r'<rul:Rule Name="[^"]+"[^>]*DataDefGroup="([^"]+)"', text)
    return m.group(1) if m else "?"


if __name__ == "__main__":
    raise SystemExit(main())
