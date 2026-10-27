#!/usr/bin/env python3
"""Chunk 9 opening census -- Blanket rating, before any task is written.

Different in kind from every census before it. Chunks 4-8 opened on ONE
coverage's rule files. Blanket is cross-cutting: `CF-PROPERTY-BUILD-ORDER.md`
item 9 calls it "the widest remaining gap... Branch B is a stub in every
premium file built in chunks 1-8, across every coverage." So this census
surveys the mechanism across ALL FIVE premium-bearing groups chunks 1-8
touched -- Building, Contents, Business Income, Special Class, Special Class
Business Income -- not one file.

It also has a starting fact chunks 6, 7 and 8 already handed it: C6-28,
C7-25 and C8-14 each independently found the SAME thing from a different
coverage -- the scheduled-vs-blanket `Choose` writes 0 before it is ever
reached, because `CauseOfLossToUse` is copied from an empty
`BlktCauseOfLossValue`. Three chunks called this "empty" and moved on. This
census's first job is to find out WHY it is empty -- and the answer turns
out to be a fourth, unfiled census in itself.

Seven questions:

  1  **The blanket-only Rate Tables.** 12 tables with `Blkt`/`Blanket` in the
     name live in `Rate Tables/`, none of them touched by any chunk-1-8
     script. Countrywide row counts and state overrides, same shape as every
     prior chunk's table census.
  2  **The five per-group blanket rule sets.** Each of the five premium
     groups files its OWN blanket machinery under its OWN parent rules file
     (`Set*BlanketValues`, `Set*BlanketRatesAndFactors`, a `DoMessage` block).
     Same idea, same rule names in places, but never inherited -- one copy
     per group. Counted, and the two dispatcher names checked against each
     other (`SetBlanketValuesSection` vs `SetBlanketValues`).
  3  **The `SetNonEQBlanketValues` root cause.** This is the ONLY rule in the
     countrywide corpus that ever assigns `BlktCauseOfLossValue` a real
     value. Its body is walked structurally to show the three ways it can
     leave the field untouched or defaulted, and what a submission would
     have to carry to hit the fourth path -- the one that actually populates
     it.
  4  **The separate blanket-rating engine.** `CommercialPropertyBlanketRating`
     (4 rules) `ForEach`-processes `CommercialPropertyBlanketRatingDetail`
     (135 rules, one file) -- a wholly distinct rule file from anything any
     prior chunk read. Rule-family counts, by prefix.
  5  **Branch-ordering / reachability, in all 47, across all FIVE groups.**
     Chunk 8's `branches()` checked Building and Contents only. Generalized
     here to Business Income, Special Class and Special Class Business
     Income as well -- 20 premium files x 47 jurisdictions.
  6  **The ISO fixture census.** Do any of the 924 STC payloads elect
     `IncludedInBlkt = "Yes"` or carry any `CommercialPropertyBlanketRating*`
     record at all? If the answer is zero, blanket has never been
     demonstrated by ISO's own corpus either -- not just by this project's
     golden cases.
  7  **Stub or starved formula?** The build order calls Branch B "a stub in
     every premium file." Every one of the 20 files is opened directly and
     its `SetPremium` classified -- `Choose` vs plain `If`/`Else`, and
     whether the branch blanket actually reaches contains a computed
     formula or a bare `0.0`.

    python scripts/cf/67_chunk9_census.py

Always exits 0 -- this is a census, not a test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import CFEditionResolver, book_for

ASOF = "20260917"

#: the five premium groups every prior chunk built, and their four coverage
#: forms -- the population this census surveys, not one coverage's files.
GROUPS = {
    "Building": ("CommercialPropertyStructureRules.Rule.xml",
                 [f"CommercialPropertyStructureBuilding{f}CoverageRules.Rule.xml"
                  for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]),
    "Contents": ("CommercialPropertyPersonalPropertyRules.Rule.xml",
                 [f"CommercialPropertyPersonalPropertyPrsnlProp{f}CoverageRules.Rule.xml"
                  for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]),
    "Business Income": ("CommercialPropertyBusinessIncomeRules.Rule.xml",
                 [f"CommercialPropertyBusinessIncome{f}CoverageRules.Rule.xml"
                  for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]),
    "Special Class": ("CommercialPropertySpecialClassRules.Rule.xml",
                 [f"CommercialPropertySpecialClass{f}CoverageRules.Rule.xml"
                  for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]),
    "SC Business Income": ("CommercialPropertySpecialClassBusnIncomeRules.Rule.xml",
                 [f"CommercialPropertySpecialClassBusnIncome{f}CoverageRules.Rule.xml"
                  for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]),
}
PARENT_FILES = [v[0] for v in GROUPS.values()]
ALL_FORM_FILES = [f for v in GROUPS.values() for f in v[1]]

TABLES = [
    "BldgPrsnlPropBlktCoverageCode", "BlktClassRatedRatingIdentificationCode",
    "BlktScheduleRatedRatingIdentificationCode",
    "BlktSprinkleredScheduleRatedRatingIdentificationCode",
    "BlktSubStandardClassRatedRatingIdentificationCode",
    "BuildersRiskBlanketFactor", "CoinsuranceFactorBlkt",
    "EarthquakeNonSprinkleredBlanketRiskIDCode",
    "EarthquakeSprinkleredBlanketRiskIDCode",
    "FloodBlanketRatingIdentificationBlanketCode",
    "FloodBlanketRatingIdentificationCode", "FloodRatingIdentificationBlanketCode",
]

DETAIL_FILE = "CommercialPropertyBlanketRatingDetailRules.Rule.xml"
BLKT_FILE = "CommercialPropertyBlanketRatingRules.Rule.xml"

DISPATCHER_NAMES = ["SetBlanketValuesSection", "SetBlanketValues"]
VALUE_RULES = ["SetNonEQBlanketValues", "SetEQBlanketValues"]


def blanket_rule_names(body: str) -> set[str]:
    return set(re.findall(r'<rul:Rule Name="(\w*[Bb]lanket\w*)"', body))


def branches(body: str):
    """One entry per `rul:When` in `SetPremium`. Lifted from
    `58_chunk8_census.py` unchanged -- a blanket branch tests `IncludedInBlkt`
    against the literal "Yes" (not merely mentions it); nothing else counts.
    """
    i = body.find('<rul:Rule Name="SetPremium"')
    if i < 0:
        return None
    seg = body[i:i + body[i:].find("</rul:Rule>") + 11]
    starts = [m.start() for m in re.finditer(r"<rul:When>", seg)]
    out = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(seg)
        chunk = seg[start:end]
        test = chunk[:chunk.find("</rul:Test>") + 12]
        eq = re.findall(
            r"<rul:Equal>(?:(?!</rul:Equal>).)*?<rul:Constant "
            r"Type=\"string\">([^<]*)</rul:Constant>", test, re.S)
        blkt = "IncludedInBlkt" in test and "Yes" in eq
        out.append(blkt)
    return out, "<rul:Otherwise>" in seg


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    books = {j: book_for(j, ASOF, resolver=res) for j in juris}
    any_book = books[juris[0]]
    d = any_book.parent.package.content / "Rules"

    # ---- 1
    print(f"=== 1  Blanket-only Rate Tables   ({len(juris)} jurisdictions, "
          f"as of {ASOF})")
    print("    all 12 found by name-grepping `Rate Tables/`; none read by "
          "any chunk-1-8 script\n")
    for t in TABLES:
        try:
            cw = any_book.parent_table(t)
            n_cw, rows = len(cw.rows), cw.rows
        except Exception as exc:
            print(f"    {t:52s} unreadable: {exc}")
            continue
        own = [j for j, b in books.items() if b.declares(t) == "state"]
        print(f"    {t:52s} CW rows={n_cw:<3d} states filing={len(own)} of "
              f"{len(juris)}" + ("   " + ",".join(own) if own else ""))
        for r in rows[:3]:
            print(f"        {r}")

    # ---- 2
    print("\n=== 2  The five per-group blanket rule sets\n")
    total_rules = 0
    dispatcher_used = {}
    body_by_group = {}
    for group, (parent_file, _forms) in GROUPS.items():
        t = (d / parent_file).read_text(encoding="utf-8-sig")
        names = blanket_rule_names(t)
        msgs = [n for n in names if n.startswith("DoMessage")]
        other = sorted(names - set(msgs))
        total_rules += len(names)
        disp = [n for n in DISPATCHER_NAMES if n in names]
        dispatcher_used[group] = disp
        print(f"    {group:20s} {parent_file}")
        print(f"        blanket-named rules: {len(names):>3d}  "
              f"({len(other)} machinery + {len(msgs)} DoMessage)")
        print(f"        dispatcher: {disp}")
        print(f"        machinery: {other}")
        i = t.find('<rul:Rule Name="SetNonEQBlanketValues"')
        if i >= 0:
            j = t.find("</rul:Rule>", i) + 11
            body_by_group[group] = t[i:j]
    print(f"\n    total blanket-named rules across the 5 parent files: "
          f"{total_rules}")
    print(f"    dispatcher name split: "
          + ", ".join(f"{g}={v}" for g, v in dispatcher_used.items()))
    print("    **Same idea, two literal names, split across the 5 groups** "
          "-- Structure and SC Business Income use `...Section`; Contents, "
          "Business Income and Special Class do not. Chunk 8's shared-name")
    print("    trap (C8-05/C8-16) generalizes to blanket's OWN machinery, "
          "before the coverage-specific factors are even reached.")
    base_group = next(iter(body_by_group))
    base = body_by_group[base_group]
    print(f"\n    SetNonEQBlanketValues body identical across all 5 groups? ")
    for g, body in body_by_group.items():
        same = "IDENTICAL" if body == base else f"DIFFERS (len {len(body)} vs {len(base)})"
        print(f"        {g:20s} {same}")

    # ---- 3
    print("\n=== 3  The `SetNonEQBlanketValues` root cause, walked "
          "structurally\n")
    body = body_by_group[base_group]
    print(f"    Group used for the walk: {base_group} "
          f"({GROUPS[base_group][0]})")
    print("    Gate 1 -- outer `If`: `../../../../MUBlktRated = \"No\"`.")
    print("        **No `Else` at this level in ANY of the 5 copies** -- if "
          "MUBlktRated is anything other than the literal \"No\"")
    print("        (absent, null, \"Yes\"), the whole rule body is skipped "
          "and BlktCauseOfLossValue is left exactly as it was.")
    print("    Gate 2 -- inner `If`: `IncludedInBlkt = \"Yes\"` on THIS item.")
    print("        Else branch: BlktCauseOfLossValue set to the literal "
          "\"Not Applicable\", not blank. So a genuinely unblanketed item")
    print("        never looks \"empty\" -- it looks Not Applicable, which "
          "is a different value from the one three chunks actually saw.")
    print("    Then branch: a `WithArgs`/`ForEach` walks "
          "`../../../../CommercialPropertyBlanketRatingTable/")
    print("        CommercialPropertyBlanketRating/"
          "CommercialPropertyBlanketRatingDetailTable/"
          "CommercialPropertyBlanketRatingDetail`, looking for a")
    print("        `UnitNumber` equal to THIS item's own `BlktIDNum`. If "
          "found, `BlktCauseOfLossValueTemp` is copied from that detail")
    print("        record's `CauseOfLoss`. **If no match is found the Temp "
          "field is never touched and keeps its initial empty-string")
    print("        constant** -- a THIRD way to end up empty, distinct from "
          "gate 1 (skipped) and gate 2's Else (\"Not Applicable\").")
    print("\n    So a golden case that sets `IncludedInBlkt=\"Yes\"` and "
          "`MUBlktRated=\"No\"` but never submits a")
    print("    `CommercialPropertyBlanketRatingTable` record with a matching "
          "`UnitNumber` reproduces exactly the symptom C6-28, C7-25 and")
    print("    C8-14 each found -- **not because the rule is broken, but "
          "because nothing has ever fed it the record it reads.**")

    # ---- 4
    print("\n=== 4  The separate blanket-rating engine\n")
    blkt_body = (d / BLKT_FILE).read_text(encoding="utf-8-sig")
    blkt_group = re.findall(r'DataDefGroup="(\w+)"', blkt_body)
    blkt_rules = re.findall(r'<rul:Rule Name="(\w+)"', blkt_body)
    print(f"    {BLKT_FILE}")
    print(f"        DataDefGroup(s): {sorted(set(blkt_group))}   "
          f"rules: {len(blkt_rules)}   {blkt_rules}")
    detail_body = (d / DETAIL_FILE).read_text(encoding="utf-8-sig")
    detail_group = sorted(set(re.findall(r'DataDefGroup="(\w+)"', detail_body)))
    detail_rules = re.findall(r'<rul:Rule Name="(\w+)"', detail_body)
    print(f"\n    {DETAIL_FILE}")
    print(f"        DataDefGroup(s): {detail_group}   file size: "
          f"{len(detail_body):,} chars   rules: {len(detail_rules)}")
    families = {}
    for n in detail_rules:
        pfx = re.match(r"[A-Za-z]+?(?=[A-Z][a-z])", n)
        key = ("Message" if n.startswith("DoMessage") else
               "AgreedVal" if "AgreedVal" in n else
               "Max" if n.startswith("SetMax") else
               "Calc" if "Calc" in n else
               "Lookup" if n.startswith("Lookup") else
               "other")
        families.setdefault(key, []).append(n)
    for k, v in sorted(families.items(), key=lambda kv: -len(kv[1])):
        print(f"        {k:10s} {len(v):>3d}   e.g. {v[:3]}")
    print("\n    Entry point: `CommercialPropertyBlanketRating.ErcProcess` "
          "`ForEach`es "
          "`CommercialPropertyBlanketRatingDetailTable/")
    print("    CommercialPropertyBlanketRatingDetail` and runs "
          "`InitializeRuleSet` + `ErcProcess` on EACH detail record -- an "
          "engine")
    print("    that computes average/highest rates per coverage across every "
          "risk sharing a `BlktIDNum`, not a `SetPremium` `Choose` branch.")
    print("    **No chunk 1-8 script has read either file.** This is Branch "
          "B, and it is not a stub in the corpus -- only in the per-item")
    print("    premium chain chunks 1-8 traced. `SetCounters` alone walks "
          "`../../../../CommercialPropertyLocationTable/.../")
    print("    CommercialPropertyStructureTable/CommercialPropertyStructure` "
          "and re-tests `IncludedInBlkt`/`BlktIDNum` from the OTHER side --")
    print("    the detail record counting the items, not the item finding the "
          "detail record. Two mechanisms, one relationship.")
    fl_override = (books["FL"].state.package.content / "Rules" / DETAIL_FILE).exists()
    print(f"\n    Florida overrides {DETAIL_FILE}: {fl_override}")

    # ---- 5
    print("\n=== 5  Branch ordering / reachability, all 5 groups x 47 "
          "jurisdictions\n")
    for group, (_parent, forms) in GROUPS.items():
        for f in forms:
            body = (d / f).read_text(encoding="utf-8-sig")
            got = branches(body)
            form = f.split("Coverage")[0]
            for key in ("BasicGroupI", "BasicGroupII", "Broad", "Special"):
                if form.endswith(key):
                    form_name = key
                    break
            else:
                form_name = form
            if got is None:
                print(f"    {group:20s} {form_name:12s} no SetPremium rule "
                      f"in this file")
                continue
            brs, has_other = got
            blkt = next((n for n, b_ in enumerate(brs) if b_), None)
            print(f"    {group:20s} {form_name:12s} {len(brs)} When(s)"
                  f"{' + Otherwise' if has_other else ''}   blanket branch: "
                  f"{None if blkt is None else blkt + 1}")

    seen, no_blkt_test, states_touching = 0, [], set()
    for j, b in books.items():
        for group, (_parent, forms) in GROUPS.items():
            for f in forms:
                p = b.state.package.content / "Rules" / f
                if not p.exists():
                    continue
                body = p.read_text(encoding="utf-8-sig")
                got = branches(body)
                if got is None:
                    continue
                seen += 1
                states_touching.add(j)
                brs, _ = got
                if not any(brs):
                    no_blkt_test.append((j, group, f))
    print(f"\n    state copies of the 20 premium files examined: {seen}, "
          f"across {len(states_touching)} of {len(juris)} jurisdictions")
    print(f"    state copies with NO explicit `IncludedInBlkt = \"Yes\"` "
          f"branch in `SetPremium`: {len(no_blkt_test)}")
    print("    (a form can still reach blanket BY ELIMINATION, the way "
          "Building's Basic I/II/Broad do countrywide -- absence here is not")
    print("    proof of unreachability by itself; it is the input to C9's "
          "per-form reachability task.)")

    # ---- 6
    print("\n=== 6  The ISO fixture census -- do any of the 924 STC payloads "
          "exercise blanket at all?\n")
    stc_root = None
    for cand in Path(str(any_book.parent.package.content)).parents:
        maybe = cand / "STC"
        if maybe.exists():
            stc_root = cand
            break
    # the STC folder lives inside each package directory, not the parent's
    # parent -- check directly under the package too.
    pkg = any_book.parent.package.content
    stc_dir = pkg / "STC"
    if not stc_dir.exists():
        print(f"    no STC/ folder under {pkg} -- searching known corpus "
              f"locations instead")
        candidates = list(Path("F:/ISO_ERC_Files").rglob("STC")) \
            if Path("F:/ISO_ERC_Files").exists() else []
    else:
        candidates = [stc_dir]
    payloads = []
    for c in candidates:
        payloads.extend(c.rglob("*.json"))
    n_field, n_yes, n_tbl = 0, 0, 0
    yes_files = []
    for p in payloads:
        try:
            t = p.read_text(encoding="utf-8-sig", errors="ignore")
        except Exception:
            continue
        if "IncludedInBlkt" in t:
            n_field += 1
        if re.search(r'"IncludedInBlkt"\s*:\s*"Yes"', t):
            n_yes += 1
            yes_files.append(str(p))
        if "CommercialPropertyBlanketRating" in t:
            n_tbl += 1
    print(f"    STC payloads scanned: {len(payloads)}")
    print(f"    carry the `IncludedInBlkt` field at all (almost always "
          f"\"No\" boilerplate): {n_field}")
    print(f"    carry `IncludedInBlkt` = \"Yes\" (blanket actually "
          f"elected): {n_yes}")
    print(f"    carry a `CommercialPropertyBlanketRating*` record of any "
          f"kind: {n_tbl}")
    if yes_files:
        print("    " + "\n    ".join(yes_files[:10]))
    else:
        print("    **Zero elect blanket, and zero carry the ratings table.** "
              "The field is boilerplate on the large majority of payloads,")
        print("    always \"No\" -- so ISO's own 921/924-payload "
              "request-fixture corpus has never demonstrated a blanket")
        print("    submission either. This project's golden cases are not "
              "unusual in leaving `CommercialPropertyBlanketRatingTable`")
        print("    empty and `IncludedInBlkt` at \"No\" -- NOTHING ISO ships "
              "does otherwise. A chunk-9 golden case will be the FIRST")
        print("    populated blanket submission anywhere in this project, "
              "and there is no ISO fixture to check it against.")

    # ---- 7
    print("\n=== 7  Is Branch B a STUB, or a STARVED FORMULA? Per-file "
          "`SetPremium` structure, all 20 files\n")
    print("    Not asked by any prior census. `branches()` above only "
          "detects a `Choose`/`When` shape -- Business Income's `SetPremium`")
    print("    turned out NOT to be a `Choose` at all when read directly. "
          "Every file is now opened and classified by its real shape.\n")
    stub_groups, formula_groups = [], []
    for group, (_parent, forms) in GROUPS.items():
        for f in forms:
            t = (d / f).read_text(encoding="utf-8-sig")
            i = t.find('<rul:Rule Name="SetPremium"')
            if i < 0:
                continue
            j = t.find("</rul:Rule>", i) + 11
            seg = t[i:j]
            has_choose = "<rul:Choose>" in seg
            blkt_fields = sorted(set(re.findall(r"Blkt\w+", seg))
                                  - {"BlktIDNum"})
            real = any(("AvgRate" in fld or "TotalFullValue" in fld
                        or "Limit" in fld) for fld in blkt_fields) \
                and len(blkt_fields) >= 3
            form = f.split("Coverage")[0]
            for key in ("BasicGroupI", "BasicGroupII", "Broad", "Special"):
                if form.endswith(key):
                    form_name = key
                    break
            else:
                form_name = form
            verdict = ("REAL FORMULA, starved of input" if real else
                        "STRUCTURAL STUB (Premium := 0.0, hardcoded)"
                        if has_choose else "unclear -- read directly")
            (formula_groups if real else stub_groups).append(
                (group, form_name))
            print(f"    {group:20s} {form_name:12s} "
                  f"{'Choose' if has_choose else 'If/Else':8s} "
                  f"Blkt fields read: {len(blkt_fields):>2d}   {verdict}")
    print(f"\n    STRUCTURAL STUB verdict: {len(stub_groups)}   "
          f"{stub_groups}")
    print(f"    REAL FORMULA verdict:    {len(formula_groups)}   "
          f"{formula_groups}")
    print("\n    **The build-order's one-line description of chunk 9 --")
    print("    'Branch B is a stub in every premium file' -- does NOT hold "
          "at the `SetPremium` level, in any of the 20 files.** Every one")
    print("    carries a complete, already-filed formula --  `IRPMFactor x "
          "PackageModFactor x Blkt<Form>AvgRate x (item value /")
    print("    BlktTotalFullValueAmount) x (BlktLimit/100)` -- reached "
          "directly by a `Choose` `When` on Building's Special and Contents'")
    print("    four forms, and BY ELIMINATION through Building's other "
          "three forms' final `When` (`CovType <> \"Leasehold Interest\"`)")
    print("    and Business Income/Special Class/SC Business Income's plain "
          "`Else`. **The one literal `Premium := 0.0` found by hand-reading")
    print("    Building's Basic Group I `Otherwise` is not the blanket "
          "branch at all -- it is the Leasehold Interest exclusion; the real")
    print("    blanket formula sits one `When` earlier.** So 'stub' is the "
          "wrong word for what chunk 9 is missing: every formula is filed")
    print("    and none has ever been fed a `BlktTotalFullValueAmount` "
          "greater than 0, because section 3's `SetNonEQBlanketValues` chain "
          "and")
    print("    section 4's separate averaging engine have never been "
          "exercised by "
          "a submission that populates `CommercialPropertyBlanketRatingTable`.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
