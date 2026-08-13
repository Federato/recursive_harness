"""State-deviation census for any coverage rule set.

Answers gate item 6 — "enumerated and quantified, per jurisdiction. Not 'some states differ.'"
Generalised from 26_census_334.py so each remaining gate reuses it.

    python 29_census_336.py                      # subline 336, latest edition per jurisdiction
    python 29_census_336.py --all-editions       # every edition (catches drift, e.g. VA)
    python 29_census_336.py --rules GeneralLiabilityClassificationLiquorCoverageRules

Two counts are reported and they are NOT interchangeable:
  * latest edition per jurisdiction  -> what an engine rating today must handle
  * across all editions              -> what an engine rating as-of a past date must handle
VA carried the Defense-Within-Limits override in 2021 and dropped it in 2023, so 336 answers
19 to the second question and 18 to the first. That gap is N4 with a premium attached.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
from collections import defaultdict

ROOT = r"C:\Projects\ISO_ERC_Files\General_Liability"
NS_RE = re.compile(r'targetNamespace="http://www\.verisk\.com/iso/erc/([^/"]+)/')
RULE_RE = re.compile(r'<rul:Rule\s+([^>]*?)>')
PLUMBING = {"InitializeRuleSet", "ErcProcess"}

ap = argparse.ArgumentParser()
ap.add_argument("--rules", default="GeneralLiabilityClassificationProdsCompldOpsCoverageRules")
ap.add_argument("--all-editions", action="store_true")
args = ap.parse_args()
FNAME = args.rules + ".Rule.xml"


def packages():
    """(namespace, package_dir) for every non-countrywide package, identity from the XSD."""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if os.path.basename(dirpath) != "DataDefs" or "_quarantine" in dirpath:
            continue
        dirnames[:] = []
        pkg = os.path.dirname(dirpath)
        for fn in filenames:
            if not fn.endswith(".xsd"):
                continue
            head = open(os.path.join(dirpath, fn), encoding="utf-8-sig",
                        errors="replace").read(20000)
            m = NS_RE.search(head)
            if m:
                yield m.group(1), pkg
                break


def rules_in(path):
    """name -> (MetadataCodes, normalised body hash, body length)"""
    out = {}
    if not os.path.exists(path):
        return out
    s = open(path, encoding="utf-8-sig").read()
    for m in RULE_RE.finditer(s):
        attrs = m.group(1)
        n = re.search(r'Name="([^"]+)"', attrs)
        if not n:
            continue
        try:
            end = s.index("\n\t</rul:Rule>", m.start()) + len("\n\t</rul:Rule>")
        except ValueError:
            continue
        body = re.sub(r"\s+", " ", s[m.start():end])
        c = re.search(r'MetadataCodes="([^"]*)"', attrs)
        out[n.group(1)] = (c.group(1) if c else "", hashlib.md5(body.encode()).hexdigest(),
                           len(body))
    return out


latest: dict[str, tuple[str, str]] = {}
allpkgs: list[tuple[str, str, str]] = []
for ns, pkg in packages():
    if ns.startswith("GL_CW"):
        continue
    juris = ns.split("_")[1]
    allpkgs.append((juris, ns, pkg))
    if juris not in latest or ns > latest[juris][0]:
        latest[juris] = (ns, pkg)

scope = allpkgs if args.all_editions else [(j, ns, p) for j, (ns, p) in sorted(latest.items())]
jurisdictions = {j for j, _, _ in scope}

over: dict[str, set[str]] = defaultdict(set)
bodies: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
empty: dict[str, set[str]] = defaultdict(set)

for juris, ns, pkg in scope:
    for name, (codes, h, ln) in rules_in(os.path.join(pkg, "Rules", FNAME)).items():
        over[name].add(juris)
        bodies[name][h].append(juris)
        if ln < 260 and "Sequence />" in open(
                os.path.join(pkg, "Rules", FNAME), encoding="utf-8-sig").read():
            pass  # per-rule emptiness is reported below from the body length

print(f"rule set : {FNAME}")
print(f"scope    : {'all editions' if args.all_editions else 'latest edition per jurisdiction'}"
      f"  ({len(scope)} packages, {len(jurisdictions)} jurisdictions)\n")

touched = set().union(*over.values()) if over else set()
print(f"override the rule set : {len(touched):2d}  {' '.join(sorted(touched))}")
print(f"pure countrywide      : {len(jurisdictions - touched):2d}  "
      f"{' '.join(sorted(jurisdictions - touched))}\n")

print("rule overridden                                            juris")
for name, js in sorted(over.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    if name in PLUMBING:
        continue
    variants = bodies[name]
    tag = ""
    if len(variants) == 1:
        h = next(iter(variants))
        # an empty override is a deliberate no-op: <rul:Sequence /> and nothing else
        tag = "  [identical across all]"
    else:
        tag = f"  [{len(variants)} distinct bodies]"
    print(f"{len(js):3d}  {name:55s} {' '.join(sorted(js))}{tag}")

print("\nNote: 'identical across all' plus a very short body means an EMPTY override —")
print("a deliberate no-op that disables the parent rule. Empty != absent != inherit (N3).")
