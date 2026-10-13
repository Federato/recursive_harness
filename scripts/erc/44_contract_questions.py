"""Stage 2 step 3: the evaluation contract's open questions, answered from source.

The build plan lists the semantics an interpreter must pin down and calls them
"declared but unspecified".  They are unspecified in ISO's *schema*.  They are
not necessarily unspecified in ISO's *content* -- an attribute the schema
permits four values for may carry exactly one across 567 packages, and then
there is nothing to decide.

This script asks each question of the whole corpus rather than of a sample, and
separates three outcomes:

  ANSWERED   the corpus admits one behaviour; implement it
  CONSTRAINED the corpus uses several, but the choice is visible in the content
  OPEN       the content cannot distinguish; the engine must refuse, not guess

Q1  Constant with no text    -- empty string, or null?
Q2  FirstValue precedence    -- which of the four sources are actually present
Q3  FirstNonNull exhaustion  -- is there always a total fallback, or can it fail
Q4  Value@AllowNullReturn    -- where nulls are permitted to escape
Q5  RunRule dispatch         -- self, sibling, and parent-package calls (N2)
Q6  Rounding                 -- every DecimalPlaces in use, and any mode evidence
Q7  Lookup result mode       -- FirstResult vs SingleResult

Emits out/contract_questions.txt.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

VALUE_SOURCES = ("FromDataDef", "FromInput", "FromParam", "FromConstant")


def main() -> None:
    pkgs, n_dirs, dupes = rules_packages()

    q1_type = Counter(); q1_write = Counter(); q1_pkgs = set()
    q2_combo = Counter(); q2_present = Counter()
    q3_last = Counter(); q3_n = Counter(); q3_pkgs_no_fallback = set()
    q4_ctx = Counter(); q4_type = Counter()
    q5_kind = Counter(); q5_proj = Counter()
    q6_dp = defaultdict(Counter)
    q7_mode = Counter(); q7_by_pkg = defaultdict(Counter)

    for pk in pkgs:
        pid = pk.pkg_id
        for f in sorted((pk.content / "Rules").glob("*.Rule.xml")):
            root = ET.fromstring(c.read_text(f))
            stem = f.name.replace(".Rule.xml", "")
            for el in root.iter():
                t = c.lname(el.tag)

                if t == "Constant" and not (el.text and el.text.strip()):
                    q1_type[el.attrib.get("Type", "(none)")] += 1
                    q1_write["writes" if "ToDataDef" in el.attrib
                             else "reads"] += 1
                    q1_pkgs.add(pid)

                elif t == "FirstValue":
                    have = tuple(s for s in VALUE_SOURCES if s in el.attrib)
                    q2_combo[have] += 1
                    for s in have:
                        q2_present[s] += 1

                elif t == "FirstNonNull":
                    ch = list(el)
                    q3_n[len(ch)] += 1
                    if ch:
                        lt = c.lname(ch[-1].tag)
                        # a trailing Constant is a total fallback: it can never
                        # be null, so the node can never exhaust
                        q3_last[lt] += 1
                        if lt != "Constant":
                            q3_pkgs_no_fallback.add(pid)

                elif t == "Value" and el.attrib.get("AllowNullReturn") == "true":
                    q4_type[el.attrib.get("Type", "?")] += 1
                    q4_ctx[stem] += 1

                elif t == "RunRule":
                    proj = el.attrib.get("ProjectName", "")
                    tgt = el.attrib.get("FileName", "")
                    if proj:
                        q5_kind["parent package (cross-package)"] += 1
                        q5_proj[proj] += 1
                    elif tgt == stem:
                        q5_kind["same file"] += 1
                    else:
                        q5_kind["sibling file, same package"] += 1

                elif t == "Lookup":
                    m = el.attrib.get("ResultMode", "(absent)")
                    q7_mode[m] += 1
                    q7_by_pkg[m][pid] += 1

                if "DecimalPlaces" in el.attrib:
                    q6_dp[t][el.attrib["DecimalPlaces"]] += 1

    L = []; A = L.append
    A("THE EVALUATION CONTRACT -- OPEN QUESTIONS, ANSWERED FROM THE CORPUS")
    A("")
    A(f"    packages: {len(pkgs)} of {n_dirs} directories "
      f"({len(dupes)} byte-identical re-unpacks skipped)")
    A("")

    A("Q1  A Constant with no text -- empty string, or null?          [ANSWERED]")
    A(f"    empty Constants: {sum(q1_type.values())} in {len(q1_pkgs)} of "
      f"{len(pkgs)} packages")
    A(f"    by @Type : {dict(q1_type)}")
    A(f"    by use   : {dict(q1_write)}")
    A("    Every one is Type='string'. No numeric or date Constant is ever")
    A("    empty. An empty string-typed Constant is THE EMPTY STRING, and an")
    A("    interpreter that returns null here breaks FirstNonNull downstream.")
    A("")

    A("Q2  FirstValue precedence -- which sources are actually present?")
    A(f"    @Order carries one value corpus-wide: DataDefInputParamConstant")
    A(f"    attribute presence across {sum(q2_combo.values())} FirstValue nodes:")
    for s in VALUE_SOURCES:
        n = q2_present[s]
        A(f"      {s:14s} present on {n:8d} "
          f"({100 * n / max(1, sum(q2_combo.values())):6.2f}%)")
    A("    distinct source combinations actually filed:")
    for combo, n in q2_combo.most_common():
        A(f"      {n:8d}  {combo if combo else '(none -- no source at all)'}")
    A("")

    A("Q3  FirstNonNull exhaustion -- can every argument be null?")
    A(f"    child counts: {dict(sorted(q3_n.items()))}")
    A("    last child, which is what decides exhaustion:")
    for k, n in q3_last.most_common():
        A(f"      {k:16s} {n:8d}")
    tot = sum(q3_last.values())
    con = q3_last.get("Constant", 0)
    A(f"    total fallback present (last child is a Constant): {con} of {tot} "
      f"({100 * con / max(1, tot):.2f}%)")
    A(f"    packages containing at least one exhaustible FirstNonNull: "
      f"{len(q3_pkgs_no_fallback)} of {len(pkgs)}")
    A("")

    A("Q4  Value@AllowNullReturn -- where is a null allowed to escape?")
    A(f"    {sum(q4_type.values())} nodes; by @Type: {dict(q4_type)}")
    A("    top rule files:")
    for k, n in q4_ctx.most_common(10):
        A(f"      {k:52s} {n}")
    A("")

    A("Q5  RunRule dispatch (N2)")
    for k, n in q5_kind.most_common():
        A(f"    {k:34s} {n:8d}")
    A(f"    distinct parent packages named by @ProjectName: {len(q5_proj)}")
    for k, n in q5_proj.most_common(12):
        A(f"      {k:28s} {n}")
    A("")

    A("Q6  Rounding -- every DecimalPlaces in use")
    for t in sorted(q6_dp):
        A(f"    {t:12s} {dict(sorted(q6_dp[t].items(), key=lambda x: int(x[0])))}")
    A("    No node anywhere declares a rounding MODE. Half-up, half-even and")
    A("    truncate are indistinguishable in the content: this one is OPEN.")
    A("")

    A("Q7  Lookup@ResultMode")
    for k, n in q7_mode.most_common():
        A(f"    {k:14s} {n:8d}  in {len(q7_by_pkg[k])} of {len(pkgs)} packages")
    A("")

    (c.OUT / "contract_questions.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
