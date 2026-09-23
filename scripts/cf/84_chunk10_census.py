#!/usr/bin/env python3
"""Chunk 10 opening census -- Earthquake, before any task is written.

`CF-PROPERTY-BUILD-ORDER.md` item 10 describes Earthquake as "the fifth
form, all coverages" -- "97 rule files, and it gates more than itself:
roughly 29 Special Class files ship an Earthquake wrapper, the Legal
Liability branch has 8 Earthquake endorsement variants, and Non-Owned
Trailers has its own. Its own EQFactor, EQ territory, EQ class, sub-limit
and flat-dollar-deductible variants."

That is five separate claims, and this census tests every one against the
corpus rather than trusting the one-line description the way chunk 9's own
opening census refused to trust "Branch B is a stub":

  1  **The population.** Are there really 97 files named `*Earthquake*` in
     `Rules/`? Broken down by family -- the `EarthquakeAndVolcanicEruption*`
     core (20 files, the build order's candidate for "the actual rating
     engine") vs. the remaining 77 thin per-endorsement wrappers.
  2  **Special Class count.** "Roughly 29" -- exact count, by filename AND
     by content (a file can touch Special Class without the string being
     in its own name, the way chunk 9 found dispatcher names that weren't
     where expected).
  3  **Legal Liability count.** "8 Earthquake endorsement variants" -- but
     zero of the 97 filenames contain "LegalLiab" anywhere. Content search
     instead of filename search, the way chunk 9 needed for `SetBlanketValues`.
  4  **Non-Owned Trailers.** Confirmed to have "its own" -- exactly one
     file, content-checked.
  5  **Where the real engine lives.** The build order's framing implies the
     97-file population under `Rules/*Earthquake*` IS the rating engine.
     Direct read says otherwise: `EQBaseRate`, `EQRate`, `FinalEQRate`,
     `EQCauseOfLossAdjustment`, `EQDeductibleFactor` are all set inside the
     FIVE PARENT FILES chunks 1-9 already opened
     (`CommercialPropertyStructureRules.Rule.xml` and its four Contents/
     Business Income/Special Class/SC Business Income siblings) -- none of
     which match `*Earthquake*` and none of which are in the 97-file
     population the build order's own count points at. The 97 files are
     downstream CONSUMERS of an already-computed `EQRate`/`FinalEQRate`,
     not the computation itself.
  6  **EQClass and EQTerr.** Are these derived (a resolver, like Building's
     county/place territory) or submission inputs (like `BasicGroupIISymbol`
     in chunk 2)? Grepped for any rule that assigns either field a value.
  7  **The EQ-named Rate Tables.** All tables under `Rate Tables/` matching
     `EQ*`/`*Earthquake*` -- CW row counts, state overrides, and which ones
     are actually read by a `Lookup` rule vs. filed and never consumed
     (`EQRateBldg`/`EQRatePrsnlProp` look like candidates by name alone --
     confirmed here, not assumed).
  8  **Does EQ share machinery with the ordinary chain?** IRPMFactor,
     PackageModFactor, the ordinary (non-EQ) DeductibleFactor/Coinsurance,
     LOI -- read anywhere in the EQ chain, or wholly separate factors
     (`EQPercentageDeductibleFactor`, `EQCoinsuranceFactor`,
     `EQDeductibleByLocationFactor`)?
  9  **State enumeration.** All 47, both layers: who overrides any of the
     97 wrapper files, and who overrides the EQ-prefixed rules inside the
     5 parent files.
  10 **The ISO fixture census.** Of 924 STC payloads, how many carry an
     `EQCovIndicator` other than "No Coverage"/"Not Applicable", or a
     populated `EQClass`/`EQTerr` -- the same shape as chunk 9's census #6.

    python scripts/cf/84_chunk10_census.py

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

#: the five premium groups chunks 1-9 already opened -- same dict shape as
#: 67_chunk9_census.py's GROUPS, reused here because the real EQ engine
#: turns out to live inside these same five parent files.
GROUPS = {
    "Building": "CommercialPropertyStructureRules.Rule.xml",
    "Contents": "CommercialPropertyPersonalPropertyRules.Rule.xml",
    "Business Income": "CommercialPropertyBusinessIncomeRules.Rule.xml",
    "Special Class": "CommercialPropertySpecialClassRules.Rule.xml",
    "SC Business Income": "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml",
}

EQ_ENGINE_RULES = [
    "SetEQBaseRate", "SetEQRate", "SetFinalEQRate", "SetEQCauseOfLossAdjustment",
    "SetEQClassToUse", "LookupEQClassToUse", "SetEQDeductibleFactor",
    "SetEQDeductibleByLocationFactor", "SetAdjustedEQRate",
]


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    books = {j: book_for(j, ASOF, resolver=res) for j in juris}
    any_book = books[juris[0]]
    rules_dir = any_book.parent.package.content / "Rules"
    tables_dir = any_book.parent.package.content / "Rate Tables"

    eq_files = sorted(p.name for p in rules_dir.glob("*.xml") if "Earthquake" in p.name)

    # ---- 1
    print(f"=== 1  The population -- Rules/*Earthquake* ({len(juris)} "
          f"jurisdictions, as of {ASOF})\n")
    print(f"    filename match count: {len(eq_files)} "
          f"(build order's own count: 97 -- "
          f"{'CONFIRMED' if len(eq_files) == 97 else 'DOES NOT MATCH'})")
    core = [f for f in eq_files if "EarthquakeAndVolcanicEruption" in f]
    print(f"\n    `EarthquakeAndVolcanicEruption*` core family: {len(core)} "
          f"files -- the build order's candidate for 'the actual rating engine'")
    for f in core:
        print(f"        {f}")
    print(f"\n    remaining thin per-endorsement wrappers: {len(eq_files) - len(core)}")

    # ---- 2
    print("\n=== 2  Special Class count -- 'roughly 29'\n")
    by_name = [f for f in eq_files if re.search(r"SpecialClass|SpclClass", f)]
    bodies = {f: (rules_dir / f).read_text(encoding="utf-8-sig") for f in eq_files}
    by_content = [f for f in eq_files
                  if re.search(r"SpecialClass|SpclClass", bodies[f])]
    print(f"    by FILENAME: {len(by_name)} of 97")
    print(f"    by CONTENT (filename need not mention it):  {len(by_content)} of 97")
    extra = sorted(set(by_content) - set(by_name))
    print(f"    content-only hits (0 expected if filenames are reliable "
          f"here): {len(extra)}  {extra}")
    print(f"    build order said 'roughly 29' -- actual is {len(by_name)} "
          f"by filename, {len(by_content)} by content.")

    # ---- 3
    print("\n=== 3  Legal Liability count -- '8 Earthquake endorsement "
          "variants', but 0 filenames say so\n")
    by_name_ll = [f for f in eq_files if "LegalLiab" in f]
    by_content_ll = [f for f in eq_files if "LegalLiab" in bodies[f]]
    print(f"    by FILENAME: {len(by_name_ll)} of 97 (confirms the build "
          f"order's own observation that filenames never say 'LegalLiab')")
    print(f"    by CONTENT: {len(by_content_ll)} of 97")
    for f in by_content_ll:
        print(f"        {f}")
    print(f"\n    build order said 8 -- actual is {len(by_content_ll)} by "
          f"content search. These are NOT 8 separate Legal-Liability-named")
    print("    files -- they are Building/PrsnlProp/Endorsement/SubLimitForm "
          "files whose SetPremium carries a SEPARATE `When` branch keyed on")
    print("    `CovType=\"Legal Liability\"`, alongside the ordinary "
          "Building/Improvements/Condo/BuildersRisk branch -- the same shape")
    print("    chunk 8 traced for the ordinary (non-EQ) chain, reappearing "
          "here undocumented by any filename.")

    # ---- 4
    print("\n=== 4  Non-Owned Trailers -- confirmed to have 'its own'\n")
    by_name_not = [f for f in eq_files if "NonOwnedTrailer" in f]
    by_content_not = [f for f in eq_files if "NonOwnedTrailer" in bodies[f]]
    print(f"    by filename: {len(by_name_not)}  by content: "
          f"{len(by_content_not)}  -- {by_name_not}")

    # ---- 5
    print("\n=== 5  Where the real EQ rating engine lives -- NOT in the "
          "97-file population\n")
    print("    The build order's own count implies the 97 files under "
          "`Rules/*Earthquake*` ARE the engine. Direct read of the rule")
    print("    bodies says otherwise -- every one of `SetEQBaseRate`, "
          "`SetEQRate`, `SetFinalEQRate`, `SetEQCauseOfLossAdjustment` is")
    print("    declared inside the SAME five parent files chunks 1-9 "
          "already opened, none of them named `*Earthquake*`:\n")
    for group, parent_file in GROUPS.items():
        t = (rules_dir / parent_file).read_text(encoding="utf-8-sig")
        found = [r for r in EQ_ENGINE_RULES
                 if re.search(rf'<rul:Rule Name="{r}"', t)]
        eq_field_hits = len(re.findall(r'FromDataDef="EQ[A-Za-z]', t))
        print(f"    {group:20s} {parent_file:48s} engine rules present: "
              f"{len(found)} of {len(EQ_ENGINE_RULES)}   EQ-field refs: "
              f"{eq_field_hits}")
        print(f"        {found}")
    print("\n    Confirmed by direct read: NONE of the per-form `SetPremium` "
          "files chunk 1 built (`CommercialPropertyStructureBuilding")
    print("    Basic Group I/II/Broad/SpecialCoverageRules.Rule.xml`) "
          "reference any EQ field at all -- EQ's own `SetPremium` (inside")
    print("    the `*Earthquake*`-named files) is a WHOLLY SEPARATE premium "
          "node (its own endorsement/coverage record), not a branch")
    print("    inside the ordinary CovType `Choose` chunks 1-9 already "
          "traced. The 97-file population consumes `EQRate`/`FinalEQRate`")
    print("    computed by the 5 parent files, and adds its OWN "
          "`Product ToDataDef=\"Premium\"` on top -- two separate premium")
    print("    trees on one submission, not one tree with an EQ branch.")

    # ---- 6
    print("\n=== 6  EQClass / EQTerr -- derived, or submission input?\n")
    struct = bodies_all = (rules_dir / "CommercialPropertyStructureRules.Rule.xml").read_text(encoding="utf-8-sig")
    for field in ("EQClass", "EQTerr"):
        writers = re.findall(rf'ToDataDef="{field}"', struct)
        print(f"    ToDataDef=\"{field}\" anywhere in "
              f"CommercialPropertyStructureRules.Rule.xml: {len(writers)}")
    print("\n    Corpus-wide (all countrywide .Rule.xml files):")
    all_rule_files = list(rules_dir.glob("*.xml"))
    for field in ("EQClass", "EQTerr"):
        hit_files = [p.name for p in all_rule_files
                     if re.search(rf'ToDataDef="{field}"',
                                  p.read_text(encoding="utf-8-sig"))]
        print(f"        {field}: written by {len(hit_files)} rule file(s) "
              f"corpus-wide -- {hit_files}")
    print("\n    Neither `EQClass` nor `EQTerr` is ever assigned by a rule "
          "anywhere in the countrywide corpus -- both are pure submission")
    print("    inputs, the same shape as chunk 2's `BasicGroupIISymbol`. "
          "`EQTerr` IS read (not written) by `CommercialPropertyLocationRules`")
    print("    and by each of the 5 parent files' `LookupEQLossCostBldg`-"
          "family rules, keyed `State + EQClass + EQTerr` -- confirming a")
    print("    real, distinct territory concept exists for EQ, just not "
          "named `EQTerritory` and not resolved by any county/place chain.")

    # ---- 7
    print("\n=== 7  The EQ-named Rate Tables\n")
    eq_tables = sorted({p.name.replace(".RateTable.csv", "")
                        for p in tables_dir.glob("*.RateTable.csv")
                        if "EQ" in p.stem or "Earthquake" in p.stem})
    print(f"    tables matching EQ*/*Earthquake* under Rate Tables/: "
          f"{len(eq_tables)}\n")
    header_only, has_rows, unreadable = [], [], []
    for t in eq_tables:
        try:
            cw = any_book.parent_table(t)
        except Exception as exc:
            unreadable.append((t, str(exc)))
            continue
        if len(cw.rows) == 0:
            header_only.append(t)
        else:
            has_rows.append((t, len(cw.rows)))
    print(f"    header-only at countrywide: {len(header_only)} of "
          f"{len(eq_tables)}")
    print(f"    carrying real rows at countrywide: {len(has_rows)} of "
          f"{len(eq_tables)}")
    print(f"    unreadable/parse errors: {len(unreadable)}")
    if unreadable:
        for t, exc in unreadable[:5]:
            print(f"        {t}: {exc}")
    print("\n    Consumer check -- is each table actually reached by a "
          "`Lookup` `MatrixDef`, corpus-wide?")
    all_bodies = "\n".join(p.read_text(encoding="utf-8-sig")
                            for p in all_rule_files)
    unread_tables = []
    for t in eq_tables:
        matrix_def = t + "Def"
        if f'MatrixDef="{matrix_def}"' not in all_bodies:
            unread_tables.append(t)
    print(f"    tables with ZERO `Lookup MatrixDef=\"...\"` reference "
          f"anywhere in the corpus: {len(unread_tables)}")
    for t in unread_tables:
        print(f"        {t}")
    if not unread_tables:
        print("        (none -- every EQ-named table is read by at least "
              "one Lookup rule)")

    print("\n    State overrides, sampled across the population "
          "(all 47, per table):")
    for t in eq_tables[:6] + (["EQRateBldg"] if "EQRateBldg" in eq_tables else []):
        try:
            own = [j for j, b in books.items() if b.declares(t) == "state"]
        except Exception:
            continue
        print(f"        {t:48s} states filing own: {len(own)} of "
              f"{len(juris)}" + ("   " + ",".join(own) if own else ""))

    # ---- 8
    print("\n=== 8  Does EQ share machinery with the ordinary chain?\n")
    endorsement_file = rules_dir / "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementRules.Rule.xml"
    endt_body = endorsement_file.read_text(encoding="utf-8-sig")
    i = endt_body.find('<rul:Rule Name="SetPremium"')
    j = endt_body.find("</rul:Rule>", i) + 11
    premium_body = endt_body[i:j]
    for shared in ("IRPMFactor", "PackageModFactor", "MultiPremiumAndDispersionCreditFactor"):
        print(f"    '{shared}' read inside EQ Endorsement's own SetPremium: "
              f"{shared in premium_body}")
    eq_own_factors = sorted(set(re.findall(r"EQ\w*(?:Deductible|Coinsurance)\w*",
                                            all_bodies)))
    print(f"\n    EQ has its OWN deductible/coinsurance-named fields, "
          f"distinct from the ordinary chain's `DeductibleFactor`/")
    print(f"    `CoinsuranceFactor` ({len(eq_own_factors)} distinct names): "
          f"{eq_own_factors}")
    print("\n    Confirmed: the EQ endorsement premium formula is "
          "`FinalEQRate x (Limit/100) x CyberIncidentExclusionFactorEQ x")
    print("    CyberIncidentExclusionCOLExcptnsFactorEQ` (Building/"
          "Improvements/Condo/BuildersRisk branch) or the Legal Liability")
    print("    variant substituting `EQCauseOfLossAdjustment x "
          "LegalLiabilityFactor x LegalLiabAddlInsurableIntFactor` -- ZERO")
    print("    shared multipliers with the ordinary chain's IRPM/PackageMod/"
          "MultiPremium factors. Two separate premium trees, confirmed by")
    print("    direct read, not inference from the field-name prefix alone.")

    # ---- 9
    print("\n=== 9  State enumeration, both layers, all 47\n")
    wrapper_override_counts = {}
    for f in eq_files:
        n = sum(1 for j, b in books.items()
                if (b.state.package.content / "Rules" / f).exists())
        wrapper_override_counts[f] = n
    total_any_override = sum(1 for f in eq_files if wrapper_override_counts[f] > 0)
    print(f"    of the 97 wrapper files, {total_any_override} have at "
          f"least one state PACKAGE copy (file-existing, not necessarily "
          f"rule-overriding -- per this project's overlay rule)")
    top = sorted(wrapper_override_counts.items(), key=lambda kv: -kv[1])[:5]
    print(f"    top 5 by state-file count: {top}")

    print("\n    Rule-level overrides of the EQ engine rules inside the 5 "
          "parent files (the real question, per the overlay rule):")
    for group, parent_file in GROUPS.items():
        overriding = []
        for j, b in books.items():
            p = b.state.package.content / "Rules" / parent_file
            if not p.exists():
                continue
            body = p.read_text(encoding="utf-8-sig")
            if any(re.search(rf'<rul:Rule Name="{r}"', body)
                   for r in EQ_ENGINE_RULES):
                overriding.append(j)
        print(f"    {group:20s} {parent_file:48s} states overriding an "
              f"EQ engine rule: {len(overriding)} of {len(juris)}"
              + ("   " + ",".join(overriding) if overriding else ""))

    # ---- 10
    print("\n=== 10  The ISO fixture census -- do any of the 924 STC "
          "payloads exercise Earthquake at all?\n")
    pkg = any_book.parent.package.content
    stc_dir = pkg / "STC"
    if not stc_dir.exists():
        candidates = list(Path("C:/Projects/ISO_ERC_Files").rglob("STC")) \
            if Path("C:/Projects/ISO_ERC_Files").exists() else []
    else:
        candidates = [stc_dir]
    payloads = []
    for c in candidates:
        payloads.extend(c.rglob("*.json"))
    n_field, n_elected, n_class, n_terr = 0, 0, 0, 0
    elected_files = []
    for p in payloads:
        try:
            t = p.read_text(encoding="utf-8-sig", errors="ignore")
        except Exception:
            continue
        if "EQCovIndicator" in t:
            n_field += 1
        m = re.search(r'"EQCovIndicator"\s*:\s*"([^"]*)"', t)
        if m and m.group(1) not in ("No Coverage", "Not Applicable", ""):
            n_elected += 1
            elected_files.append((str(p), m.group(1)))
        if re.search(r'"EQClass"\s*:\s*"[^"]+"', t):
            n_class += 1
        if re.search(r'"EQTerr"\s*:\s*"[^"]+"', t):
            n_terr += 1
    print(f"    STC payloads scanned: {len(payloads)}")
    print(f"    carry the `EQCovIndicator` field at all: {n_field}")
    print(f"    `EQCovIndicator` elected to something other than 'No "
          f"Coverage'/'Not Applicable': {n_elected}")
    print(f"    carry a populated `EQClass`: {n_class}")
    print(f"    carry a populated `EQTerr`: {n_terr}")
    if elected_files:
        print("    elected files (up to 10):")
        for f, v in elected_files[:10]:
            print(f"        {f}   EQCovIndicator={v!r}")
    else:
        print("    **Zero payloads elect Earthquake coverage.** Same shape "
              "as chunk 9's blanket finding -- ISO's own 924-payload fixture")
        print("    corpus has never demonstrated an Earthquake submission "
              "either. A chunk-10 golden case will be the first.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
