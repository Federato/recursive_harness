"""Census: which jurisdictions override the Premises/Operations (334) rating rules,
which rules they override, and what CW parent each package names.

ERC is the source. Nothing here is inferred from a directory name: package identity
comes from the XSD targetNamespace, and the parent from its xs:import.
"""
import os, re, json, sys
from collections import defaultdict

ROOT = r"C:\Projects\ISO_ERC_Files\General_Liability"
PREMOPS = "GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml"
CLASSIF = "GeneralLiabilityClassificationRules.Rule.xml"

NS_RE = re.compile(r'targetNamespace="http://www\.verisk\.com/iso/erc/([^/"]+)/')
IMP_RE = re.compile(r'schemaLocation="erc://([^/"]+)/')
RULE_RE = re.compile(r'<rul:Rule Name="([^"]+)"[^>]*?(?:MetadataCodes="([^"]*)")?[^>]*>')


def rule_index(path):
    """name -> MetadataCodes, from a .Rule.xml"""
    out = {}
    try:
        s = open(path, encoding="utf-8-sig").read()
    except OSError:
        return out
    for m in re.finditer(r'<rul:Rule\s+([^>]*?)>', s):
        attrs = m.group(1)
        n = re.search(r'Name="([^"]+)"', attrs)
        c = re.search(r'MetadataCodes="([^"]*)"', attrs)
        if n:
            out[n.group(1)] = c.group(1) if c else ""
    return out


def find_packages():
    """yield (pkgdir, juris_from_ns, edition, version, parent_ns)"""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if os.path.basename(dirpath) != "DataDefs":
            continue
        if "_quarantine" in dirpath:
            continue
        pkg = os.path.dirname(dirpath)
        ns = parent = None
        for fn in filenames:
            if not fn.endswith(".xsd"):
                continue
            s = open(os.path.join(dirpath, fn), encoding="utf-8-sig", errors="replace").read(20000)
            m = NS_RE.search(s)
            if m and ns is None:
                ns = m.group(1)
            for im in IMP_RE.finditer(s):
                if im.group(1).startswith("GL_CW") or im.group(1).startswith("GL CW"):
                    parent = im.group(1)
        if ns:
            yield pkg, ns, parent
        dirnames[:] = []


cw_rules = {}
rows = []
for pkg, ns, parent in find_packages():
    rules = os.path.join(pkg, "Rules")
    po = rule_index(os.path.join(rules, PREMOPS))
    cl = rule_index(os.path.join(rules, CLASSIF))
    rows.append(dict(pkg=pkg, ns=ns, parent=parent, po=po, cl=cl))

print(f"packages scanned: {len(rows)}")
cw = [r for r in rows if r["ns"].startswith("GL_CW")]
st = [r for r in rows if not r["ns"].startswith("GL_CW")]
print(f"  countrywide: {len(cw)}   state: {len(st)}")
print(f"  state packages carrying a PremOps override file: {sum(1 for r in st if r['po'])}")
print(f"  state packages carrying a Classification override file: {sum(1 for r in st if r['cl'])}")

# which rules do states override, and how often
po_over = defaultdict(set)
for r in st:
    juris = r["ns"].split("_")[1] if "_" in r["ns"] else r["ns"]
    for name, codes in r["po"].items():
        po_over[name].add(juris)

print("\n=== PremOps rules overridden at state level (rule -> #jurisdictions) ===")
for name, js in sorted(po_over.items(), key=lambda kv: -len(kv[1])):
    print(f"{len(js):3d}  {name:60s} {' '.join(sorted(js))}")

# reproduces docs/gates/GATE-334-PREMISES-OPERATIONS.md sec.6
json.dump([{k: (v if k != "po" and k != "cl" else sorted(v)) for k, v in r.items()} for r in rows],
          open("census_334.json", "w"), indent=1)
