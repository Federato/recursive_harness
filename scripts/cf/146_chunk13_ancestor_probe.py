"""OI-111 probe: what does `ancestor::Name` mean in CF?

The engine (gl_engine/interp/tree.py) reads every `ancestor::X` as "restart at
the document root", which is right for GL's `ancestor::MasterGLCW/Policy`
(the name is the schema's, and never matches the real root). CF also writes
`ancestor::CommercialProperty/...` and `ancestor::CommercialPropertyStructure/...`
-- names of real records in the tree. Read as "the root", every one of those
lands on nothing.

This probe does NOT change the engine. It patches `tree.select` in-process
only, to the competing reading -- "the nearest ancestor-or-self whose tag is
Name; the root if there is none" (which keeps GL's MasterGLCW behaviour) --
and rates the same submissions both ways. Where the two readings give
different answers, the stored ISO response says which one ISO uses.

    python scripts/cf/146_chunk13_ancestor_probe.py
"""
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from gl_engine.interp import tree

rp = import_module("145_chunk13_c13-03_replay")
ORIG = tree.select
ORIG_ENSURE = tree.ensure
AX = re.compile(r"^(?P<pre>/?)ancestor::(?P<name>[A-Za-z0-9_]+)(?P<rest>/.*)?$")


def named_ancestor_select(path, context):
    m = AX.match(path or "")
    if m:
        n = context
        while n is not None and n.tag != m["name"]:
            n = n.parent
        if n is not None:
            rest = (m["rest"] or "").lstrip("/")
            return ORIG(rest, n) if rest else [n]
    return ORIG(path, context)


def named_ancestor_ensure(path, context):
    m = AX.match(path or "")
    if m:
        n = context
        while n is not None and n.tag != m["name"]:
            n = n.parent
        if n is not None:
            rest = (m["rest"] or "").lstrip("/")
            return ORIG_ENSURE(rest, n) if rest else n
    return ORIG_ENSURE(path, context)


def run(name, patched):
    tree.select = named_ancestor_select if patched else ORIG
    tree.ensure = named_ancestor_ensure if patched else ORIG_ENSURE
    try:
        req = json.loads((rp.RESULTS / f"{name}_request.json").read_text(encoding="utf-8-sig"))
        resp = json.loads((rp.RESULTS / f"{name}_response.json").read_text(encoding="utf-8-sig"))
        st, eff, ours = rp.replay(req, None)
        return rp.iso_fields(resp), ours
    finally:
        tree.select = ORIG
        tree.ensure = ORIG_ENSURE


def main():
    for name in ["chunk12_oi108_CA_blanket", "chunk12_oi108_CA_scheduled", "chunk12_oi108_GA_blanket", "NY_terrorism"]:
        iso, root_read = run(name, False)
        _, named_read = run(name, True)
        print(f"\n{name}")
        keys = sorted(k for k in iso if re.search(r"ZzDisclosure|PostTRIA", k) or iso[k])
        for k in keys:
            a, b, c = iso[k], root_read.get(k), named_read.get(k)
            if rp.num(a) == rp.num(b) == rp.num(c):
                continue
            print(f"   {k.replace('CommercialProperty', '')[-80:]:80s} ISO {a!s:>8s}  root-read {b!s:>8s}  "
                  f"named-ancestor {c!s:>8s}")
        agree_root = all(rp.num(iso[k]) == rp.num(root_read.get(k)) or (rp.num(iso[k]) in (0, None) and rp.num(root_read.get(k)) in (0, None)) for k in iso)
        agree_named = all(rp.num(iso[k]) == rp.num(named_read.get(k)) or (rp.num(iso[k]) in (0, None) and rp.num(named_read.get(k)) in (0, None)) for k in iso)
        print(f"   all terrorism fields = ISO?   root-read: {agree_root}   named-ancestor: {agree_named}")


if __name__ == "__main__":
    main()
