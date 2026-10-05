"""Extract the premium roll-up tree plus the per-state overlay, for one line.

    python scripts/premium/02_premium_tree.py --line GL
    python scripts/premium/02_premium_tree.py --line CF

Writes a JSON payload next to this script; 03 renders it. Read-only."""
import re, os, glob, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


import argparse
LINES = {
    "GL": dict(root_dir=r"F:/ISO_ERC_Files/General_Liability", root="GeneralLiability",
               pat=r"^GL[ _]?([A-Z]{2})[ _]?(\d{8})[ _]?V(\d+)$", cw="GL CW *"),
    "CF": dict(root_dir=r"F:/ISO_ERC_Files/CF", root="CommercialProperty",
               pat=r"^CF[ _]?([A-Z]{2})[ _]?(\d{8})[ _]?V(\d+)$", cw="CF *"),
}
_ap = argparse.ArgumentParser()
_ap.add_argument("--line", choices=sorted(LINES), default="GL")
_A = _ap.parse_args()
_C = LINES[_A.line]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = _C["root_dir"]
ROOT = _C["root"]
PAT = re.compile(_C["pat"])
JSON_OUT = os.path.join(HERE, "_tree_%s.json" % _A.line)


def latest():
    best = {}
    for dp, dn, fn in os.walk(ROOT_DIR):
        if os.path.basename(dp) != "DataDefs":
            continue
        p = os.path.dirname(dp)
        m = PAT.match(os.path.basename(p))
        if not m:
            continue
        st, dt, v = m.group(1), m.group(2), int(m.group(3))
        if st not in best or (dt, v) > (best[st][0], best[st][1]):
            best[st] = (dt, v, p)
    return best


def rule(text, name):
    i = text.find('Name="%s"' % name)
    if i < 0:
        return ""
    j = text.find("</rul:Rule>", i)
    return text[i:j] if j > 0 else text[i:]


def scan(pkg):
    """group -> {children, aggregates, own, setpremium...} for one package."""
    out = {}
    for path in sorted(glob.glob(os.path.join(pkg, "Rules", "*.xml"))):
        t = open(path, encoding="utf-8", errors="replace").read()
        calc = rule(t, "CalculateTotalPremium")
        sp_probe = rule(t, "SetPremium")
        # A state package ships only what changed: a file overriding SetPremium need not
        # re-declare CalculateTotalPremium. Requiring the latter drops those groups.
        if not calc and not sp_probe:
            continue
        src = calc or sp_probe
        g = re.search(r'DataDefGroup="([^"]+)"', src[:300])
        g = g.group(1) if g else os.path.basename(path).replace("Rules.Rule.xml", "")
        rep = set(re.findall(r'<rul:ForEach AtDataDef="([A-Za-z0-9]+)Table/', calc))
        sing = set(re.findall(r'<rul:Locate AtDataDef="([A-Za-z0-9]+)"', calc))
        sp = rule(t, "SetPremium")
        scope = re.search(r'MetadataCodes="([^"]+)"', sp[:300]) if sp else None
        out[g] = {
            "children": sorted(rep | sing),
            "rep": len(rep), "sing": len(sing),
            "agg": 'ToDataDef="ErcCalculatedTotalPremium"' in calc,
            "own": 'FromDataDef="Premium"' in calc,
            "sp": len(sp),
            "sp_scope": scope.group(1) if scope else "",
            "inputs": sorted(set(re.findall(r'FromDataDef="([A-Za-z0-9/\.]+)"', sp)))[:14] if sp else [],
        }
    return out


pkgs = latest()
cw = scan(pkgs["CW"][2])
print("CW groups with a premium roll-up:", len(cw))

# ---- state overlay -----------------------------------------------------------
overrides = collections.defaultdict(list)   # group -> [states overriding SetPremium]
state_only = collections.defaultdict(list)  # group -> [states where it exists but CW does not]
state_counts = {}
for st, (dt, v, d) in sorted(pkgs.items()):
    if st == "CW":
        continue
    s = scan(d)
    state_counts[st] = {"groups": len(s), "new": 0, "over": 0,
                        "pkg": os.path.basename(d), "eff": dt[:4] + "-" + dt[4:6] + "-" + dt[6:]}
    for g, n in s.items():
        if g not in cw:
            state_only[g].append(st)
            state_counts[st]["new"] += 1
        elif n["sp"] and n["sp_scope"] == "RuleTypeOverridden":
            overrides[g].append(st)
            state_counts[st]["over"] += 1
    print("  %s %-22s groups %3d  new %3d  overrides %d"
          % (st, state_counts[st]["pkg"], len(s), state_counts[st]["new"], state_counts[st]["over"]))

# ---- depth + parents ---------------------------------------------------------
depth, parent = {ROOT: 0}, {}
q = collections.deque([ROOT])
while q:
    g = q.popleft()
    for c in cw.get(g, {}).get("children", []):
        if c not in depth:
            depth[c] = depth[g] + 1
            parent[c] = g
            q.append(c)

nodes = {}
for g, n in cw.items():
    nodes[g] = {
        "n": g,
        "d": depth.get(g, -1),
        "a": 1 if n["agg"] else 0,
        "o": 1 if n["own"] else 0,
        "s": n["sp"],
        "rep": n["rep"], "sing": n["sing"],
        "c": [c for c in n["children"] if c in cw],
        "ov": sorted(overrides.get(g, [])),
        "in": n["inputs"],
    }

# state-only groups, attached as a flat list per state (their parents are state files)
so = collections.defaultdict(list)
for g, sts in state_only.items():
    for st in sts:
        so[st].append(g)
for st in so:
    so[st] = sorted(so[st])

payload = {
    "root": ROOT,
    "pkg": os.path.basename(pkgs["CW"][2]),
    "nodes": nodes,
    "stateOnly": so,
    "stateCounts": state_counts,
    "overrideGroups": {g: sorted(v) for g, v in overrides.items()},
}

print()
print("nodes:", len(nodes), "| max depth:", max(depth.values()))
print("groups any state overrides SetPremium on:", len(overrides))
print("state-only premium groups (distinct):", len(state_only))
open(JSON_OUT, "w", encoding="utf-8").write(json.dumps(payload, separators=(",", ":")))
print("json written")
