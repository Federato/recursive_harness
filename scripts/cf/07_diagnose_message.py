#!/usr/bin/env python3
"""Diagnose a CF validation message: find the rule, decode it, test it against a payload.

ISO returns every message as an "Error", with a text and a `TableName`, and no
indication of what in the submission caused it. Working that out by hand takes
an hour: find the rule among ~1,600, read nested `<rul:Test>` XML, then compare
each branch against the payload by eye. This does that in one command.

    python scripts/cf/07_diagnose_message.py --message "CP 03 20 Must Be Attached ..." \\
                                             --state AL \\
                                             --payload CF_Algorithm/sample_payloads/x.json

    python scripts/cf/07_diagnose_message.py --rule DoMessageCP0320MustBe... --state AL

What it reports:
  * the rule, its file, its datadef group, and whether the state overrides or
    suppresses the countrywide version;
  * the condition decoded into readable pseudo-code;
  * every `<field> <op> <constant>` comparison in it, with the value the payload
    actually supplies and whether that comparison is TRUE;
  * every endorsement record the rule requires or forbids, and whether the
    payload carries it.

It does **not** evaluate the rule. Nesting and And/Or structure are shown, not
resolved -- the operator still decides which branch matters. That is deliberate:
a partial evaluator that silently mis-handles a nested Or would be worse than
none. Exit 0 always; this is a diagnostic.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CORPUS = os.environ.get("CF_ERC_ROOT", r"F:\ISO_ERC_Files\CF")
PKGPAT = re.compile(r"^CF[ _]?([A-Z]{2})[ _]?(\d{8})[ _]?V(\d+)$")


def latest_packages() -> dict:
    """Newest (effective date, version) package per jurisdiction."""
    best = {}
    for d in glob.glob(os.path.join(CORPUS, "*", "CF *")) + glob.glob(os.path.join(CORPUS, "*", "CFCW*")):
        m = PKGPAT.match(os.path.basename(d))
        if not m:
            continue
        st, dt, v = m.group(1), m.group(2), int(m.group(3))
        if st not in best or (dt, v) > (best[st][0], best[st][1]):
            best[st] = (dt, v, d)
    return best


def find_rules(pkg_dir: str, wanted_rule: str | None, wanted_msg: str | None):
    """Every DoMessage rule in a package matching a rule name or message text."""
    hits = []
    for path in sorted(glob.glob(os.path.join(pkg_dir, "Rules", "*.xml"))):
        t = open(path, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'<rul:Rule Name="(DoMessage[A-Za-z0-9_]*)"([^>]*)>', t):
            name, attrs = m.group(1), m.group(2)
            end = t.find("</rul:Rule>", m.end())
            body = t[m.end():end] if end > 0 else ""
            msg = re.search(r'Param="Message">\s*<rul:Constant Type="string">(.*?)</rul:Constant>', body, re.S)
            text = msg.group(1).strip() if msg else ""
            if wanted_rule and name.lower() != wanted_rule.lower():
                continue
            if wanted_msg and _norm(wanted_msg) not in _norm(text):
                continue
            grp = re.search(r'DataDefGroup="([^"]+)"', attrs)
            meta = re.search(r'MetadataCodes="([^"]+)"', attrs)
            hits.append({
                "rule": name, "file": os.path.basename(path), "body": body, "text": text,
                "group": grp.group(1) if grp else "", "scope": meta.group(1) if meta else "",
            })
    return hits


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def decode(cond: str) -> str:
    """Nested rule XML into something a person can read."""
    s = cond
    s = re.sub(r'<rul:(?:First)?Value[^>]*FromDataDef="([^"]+)"[^>]*/>', r"[\1]", s)
    s = re.sub(r'<rul:Value[^>]*FromParam="([^"]+)"[^>]*/>', r"<param:\1>", s)
    s = re.sub(r'<rul:Constant[^>]*>([^<]*)</rul:Constant>', r'"\1"', s)
    s = re.sub(r'<rul:Constant[^>]*/>', '""', s)
    s = re.sub(r'<rul:(Exist|NotExist) AtInputDataDef="([^"]+)"\s*/>', r"\1(\2)", s)
    s = re.sub(r"<rul:(\w+)>", r" \1( ", s)
    s = re.sub(r"</rul:(\w+)>", r" )", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def collect_values(payload, group: str) -> list:
    """Every record of `group` in the payload, as flat dicts of its scalars."""
    out = []

    def walk(node, name):
        if isinstance(node, dict):
            if name == group:
                out.append({k: v for k, v in node.items() if not isinstance(v, (dict, list))})
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    walk(v, k)
        elif isinstance(node, list):
            for it in node:
                walk(it, name)

    body = payload.get("body", payload)
    for k, v in body.items():
        if isinstance(v, (dict, list)):
            walk(v, k)
    return out


def records_present(payload) -> set:
    """Names of every child record the payload carries at least one of."""
    seen = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    seen.add(k)
                    walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(payload.get("body", payload))
    return seen


_OPS = r"Equal|NotEqual|GreaterThan|LessThan|GreaterThanOrEqual|LessThanOrEqual"
# field vs literal
COMPARE = re.compile(
    r'<rul:(%s)>\s*'
    r'<rul:(?:First)?Value[^>]*FromDataDef="([^"]+)"[^>]*/>\s*'
    r'<rul:Constant[^>]*>([^<]*)</rul:Constant>' % _OPS, re.S)
# field vs field -- the half that decides most deductible rules, and the easiest to miss
COMPARE2 = re.compile(
    r'<rul:(%s)>\s*'
    r'<rul:(?:First)?Value[^>]*FromDataDef="([^"]+)"[^>]*/>\s*'
    r'<rul:(?:First)?Value[^>]*FromDataDef="([^"]+)"[^>]*/>' % _OPS, re.S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", help="message text as returned by RAaS (substring match)")
    ap.add_argument("--rule", help="exact DoMessage rule name")
    ap.add_argument("--state", default="CW", help="jurisdiction to resolve the rule in")
    ap.add_argument("--table", help="TableName from the RAaS response -- the datadef group "
                                    "that raised it. Strongly recommended: the same message "
                                    "text is filed on several coverages.")
    ap.add_argument("--payload", help="submission JSON to test the condition against")
    a = ap.parse_args()
    if not (a.message or a.rule):
        ap.error("give --message or --rule")

    pkgs = latest_packages()
    st = a.state.upper()
    if st not in pkgs:
        print("no package for %s; have %s" % (st, ", ".join(sorted(pkgs))))
        return 0

    state_hits = find_rules(pkgs[st][2], a.rule, a.message) if st != "CW" else []
    cw_hits = find_rules(pkgs["CW"][2], a.rule, a.message)
    if a.table:
        state_hits = [h for h in state_hits if h["group"] == a.table]
        cw_hits = [h for h in cw_hits if h["group"] == a.table]

    # A state override with an empty body suppresses the countrywide message.
    for h in state_hits:
        if len(h["body"].strip()) < 60 and not h["text"]:
            h["suppressed"] = True

    hits = state_hits or cw_hits
    if not hits:
        print("no matching DoMessage rule in %s or CW" % st)
        return 0

    print("=" * 78)
    print("%s package: %s" % (st, os.path.basename(pkgs[st][2])))
    print("matched %d rule(s)%s" % (len(hits), " in the state package" if state_hits else " countrywide"))

    payload = json.load(open(a.payload, encoding="utf-8")) if a.payload else None
    present = records_present(payload) if payload else set()

    for h in hits:
        print()
        print("-" * 78)
        print("rule   : %s" % h["rule"])
        print("file   : %s   scope: %s" % (h["file"], h["scope"]))
        print("group  : %s" % h["group"])
        print("message: %s" % (h["text"] or "(none -- this override emits nothing)"))
        if h.get("suppressed"):
            print()
            print(">>> %s SUPPRESSES this countrywide message (empty override body)." % st)
            print(">>> It cannot fire in %s. If RAaS returned it, check the state you sent." % st)
            continue

        k = h["body"].find("<rul:Then>")
        cond = h["body"][:k] if k > 0 else h["body"]

        print()
        print("condition:")
        print("  " + decode(cond))

        cmps = COMPARE.findall(cond)
        if cmps:
            print()
            print("field comparisons%s:" % (" vs payload" if payload else ""))
            recs = collect_values(payload, h["group"]) if payload else []
            if payload and not recs:
                print("  (payload carries no %s record -- this rule cannot apply to it)" % h["group"])
            for op, field, const in cmps:
                line = "  [%s] %s %r" % (field, op, const)
                if field.startswith("../"):
                    line += "   (ancestor field -- resolve by hand)"
                elif recs:
                    vals = [r.get(field) for r in recs if field in r]
                    if vals:
                        truths = []
                        for v in vals:
                            t = (str(v) == const) if op == "Equal" else (str(v) != const) if op == "NotEqual" else None
                            truths.append("TRUE" if t else "false" if t is False else "?")
                        line += "   payload=%r -> %s" % (vals[0] if len(vals) == 1 else vals, ", ".join(truths))
                    else:
                        line += "   (field absent from the payload's %s record)" % h["group"]
                print(line)

        cmps2 = COMPARE2.findall(cond)
        if cmps2:
            print()
            print("field-to-field comparisons%s:" % (" vs payload" if payload else ""))
            recs = collect_values(payload, h["group"]) if payload else []
            for op, f1, f2 in cmps2:
                line = "  [%s] %s [%s]" % (f1, op, f2)
                if recs and not f1.startswith("../") and not f2.startswith("../"):
                    r0 = recs[0]
                    if f1 in r0 and f2 in r0:
                        v1, v2 = str(r0[f1]), str(r0[f2])
                        t = (v1 == v2) if op == "Equal" else (v1 != v2) if op == "NotEqual" else None
                        line += "   payload: %r vs %r -> %s" % (
                            r0[f1], r0[f2], "TRUE" if t else "false" if t is False else "?")
                    else:
                        missing = [f for f in (f1, f2) if f not in r0]
                        line += "   (not in payload: %s)" % ", ".join(missing)
                print(line)

        for tag, label in (("NotExist", "requires record"), ("Exist", "forbids record")):
            for rec in re.findall(r'<rul:%s AtInputDataDef="([^"]+)"' % tag, cond):
                leaf = rec.split("/")[-1]
                mark = ""
                if payload:
                    has = leaf in present
                    if tag == "NotExist":
                        mark = "   payload HAS it -> condition false (message suppressed)" if has \
                               else "   payload LACKS it -> condition TRUE (contributes to the message)"
                    else:
                        mark = "   payload HAS it -> condition TRUE" if has else "   payload lacks it -> false"
                print("  %s: %s%s" % (label, leaf, mark))

    print()
    print("Reminder: this shows the facts, it does not evaluate And/Or nesting.")
    print("Check whether a mirrored rule exists before attaching a form to silence a message.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
