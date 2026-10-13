#!/usr/bin/env python3
"""Chunk 10, C10-17 -- Non-Owned Trailers' own EQ file, traced end to end.

The census (`84_chunk10_census.py`) and C10-10's direct read
(`94_chunk10_c10-10_population_read.py`) both name exactly ONE file by
content search: `CommercialPropertyNonOwnedTrailersEarthquakeCoverageRules.
Rule.xml`. C10-10 flagged it as "STRUCTURALLY DIFFERENT -- its own
`SetPremium` is a 3-way `Choose` mirroring BUILDING's own top-level EQ
`SetPremium` shape in miniature ... not a re-run of Building's chain (it has
its own `LimitThreshold`/`LimitToUse` derivation) but the SAME 3-branch
shape." This task reads the FULL file (not just `SetPremium`) and settles
the question C10-10 only flagged.

**Finding 1, decisive and not named by the census or C10-10**: this file's
`DataDefGroup` is `CommercialPropertyNonOwnedTrailersEarthquakeCoverage`,
attached under `CommercialPropertyPersonalProperty` (CONTENTS), confirmed by
a corpus-wide search for who else references this table -- only
`CommercialPropertyPersonalPropertyRules.Rule.xml` (its `ErcProcess`
`Locate`s the record as a peer of `CommercialPropertyNonOwnedTrailersCoverage`/
`...BasicGroupI/IICoverage`/`...BroadCoverage`/`...SpecialCoverage`, the
ordinary non-EQ Non-Owned Trailers forms) and
`CommercialPropertyHigherLimitsPersonalPropertyRules.Rule.xml` (an optional
limit override). It is NOT a Structure-level record at all -- every `../`
in its own `SetPremium` (`EQCauseOfLossAdjustment`, `FinalEQRate`,
`BlktEQAvgRate`, `LegalLiabFactor`, `LegalLiabAddlInsurableIntFactor`)
resolves to the PARENT Personal Property record's OWN already-computed EQ
chain -- confirmed by the field name itself: `LegalLiabFactor` (no "ility"),
which is written by exactly one rule corpus-wide,
`CommercialPropertyPersonalPropertyRules.Rule.xml`'s own `SetLegalLiabFactor`
-- the CONTENTS-side name C8-01 already distinguished from Building's
`LegalLiabilityFactor`. Non-Owned Trailers is a Contents coverage FORM
(its own `CovType="Non-Owned Trailers"` value, confirmed legal against
`DomainCovTypePrsnlProp.DomainTable.csv` for
`CovForm="Building and Personal Property Coverage Form"`), a peer of
Contents' Basic/Broad/Special forms, not a Building-side rider at all.

**Finding 2**: it genuinely does NOT re-run Building's or Contents' own
base-rate-to-final-rate chain -- no `Lookup` of its own anywhere in the
file. It reads exactly whichever of Contents' `FinalEQRate` (plain),
`BlktEQAvgRate` (blanket) or `EQCauseOfLossAdjustment x LegalLiabFactor x
LegalLiabAddlInsurableIntFactor` (Legal Liability form) the PARENT record
already computed, the identical 3-way switch shape as Building's own EQ
Endorsement `SetPremium` -- confirming C10-10's "mirrors Building's
top-level EQ SetPremium shape in miniature" characterization exactly.

**Finding 3, the genuinely separate machinery**: `LimitThreshold`/
`LimitToUse` and the `(LimitToUse - LimitThreshold)/100` subtraction ARE its
own -- no other EQ file in the 97-file population subtracts a threshold
before dividing by 100. `LimitThreshold` is looked up from a real, tiny
filed table (`NonOwnedTrailersLimitThreshold`, one CW row confirmed below,
$5,000) via its own `LookupNonOwnedTrailersLimitThreshold` rule, and the
`SetPremium` outer gate (`LimitToUse > LimitThreshold`) is a genuine THIRD
zero-case this project has not logged for EQ before -- a populated,
matching `EQClass`/`EQTerr` chain can still return $0 if the trailer limit
elected does not exceed the state's own filed threshold.

**Verdict**: genuinely separate machinery for the threshold/limit gate,
genuinely NOT separate for the rate itself -- it is a thin consumer of
Contents' own EQ chain (the same one C10-11 already proved), wearing its
own eligibility gate on top. Neither "wholly separate" nor "a re-run" is
the right description; "peer coverage form with its own eligibility gate,
reading a shared rate" is.

**Finding 4, found only by running, and a genuine surprise against the
naive reading of the file**: the coverage record's own `Limit` field --
the obvious candidate for "the trailer sub-limit" -- is NOT what
`SetLimitToUse` reads for the plain or blanket branches. `SetLimitToUse`'s
`Otherwise` (no Higher-Limits-Personal-Property override, no Legal
Liability `CovForm`) copies `../EQLimitToUse` -- the PARENT Personal
Property record's OWN full EQ limit -- not this record's `Limit` at all.
A first run of this script set `Limit=50000` on the coverage record
expecting it to cap `LimitToUse`; the engine instead used Contents' own
full `Limit` (100,000, chunk 4's own value) for `LimitToUse`, confirmed by
reading the actual result before asserting anything further. The `Limit`
field on this record is read ONLY by the Legal Liability `CovForm` branch,
and even there it reads `../Limit` (the parent's), never the local field --
so `Limit` here is functionally a domain-hygiene/reporting field for the
plain and blanket paths, not a load-bearing sub-limit. This is exactly the
project's own standing "no-op trap" shape (chunk 1's own two zeros, C10-01's
three), just discovered on a field that looked load-bearing from the name
alone.

This script builds ONE real submission -- chunk 4's own Contents case
(`22_chunk4_golden_case.py`, Basic form), with the Personal Property item's
`CovType` switched to `"Non-Owned Trailers"`, chunk 10's own EQ election
added (reusing `95_chunk10_c10-11_all_groups_chain.py`'s `contents_predict`/
`contents_submission` machinery), and a `CommercialPropertyNonOwnedTrailers
EarthquakeCoverage` record attached (its own `Limit` field set, but --
per finding 4 -- not load-bearing here) -- and confirms the premium by hand
BEFORE running, using the mechanism actually read off the XML:

    LimitToUse  = ../EQLimitToUse  (Contents' OWN full EQ limit, NOT this
                                     record's own Limit field)
    Premium     = round(round(round(FinalEQRate x (LimitToUse-Threshold)/100, 0)
                              x CyberIncidentExclusionFactorEQ, 0)
                        x CyberIncidentExclusionCOLExcptnsFactorEQ, 0)

    python scripts/cf/101_chunk10_c10-17_non_owned_trailers.py [--trace]

Exit 0 on match. No engine code touched regardless of outcome.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk10_all = import_module("95_chunk10_c10-11_all_groups_chain")

JURIS, ASOF = chunk10_all.JURIS, chunk10_all.ASOF

PP = chunk10_all.CONTENTS_PP
#: NOT a "...Table/...[1]" collection entry -- confirmed by running (finding 5
#: below) that `CommercialPropertyNonOwnedTrailersEarthquakeCoverage` is a
#: SINGLETON child the engine auto-instantiates under Personal Property,
#: the same shape as its four sibling Non-Owned Trailers coverage forms
#: (Basic I/II, Broad, the ordinary non-EQ form) -- there is no `Table`
#: wrapper for any of the five, unlike Building's own EQ Endorsement.
NOT_ENDT = PP + "/CommercialPropertyNonOwnedTrailersEarthquakeCoverage"
CONTENTS_BASIC_PREM = (PP + "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage"
                             "/Premium")

RECORD_LIMIT = 50_000       # set on the coverage record itself -- NOT load-bearing
                             # for the plain/blanket branches; see finding 4.
PARENT_LIMIT = 100_000      # Contents' own Limit (chunk 4), what LimitToUse
                             # ACTUALLY resolves to via ../EQLimitToUse
LIMIT_THRESHOLD = 5_000      # NonOwnedTrailersLimitThreshold [CW], confirmed below


def submission() -> dict:
    """Chunk 10's own Contents submission (C10-11), with the Personal
    Property item's CovType switched to Non-Owned Trailers and its own
    Earthquake coverage record attached alongside."""
    sub = chunk10_all.contents_submission()
    struct = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
              ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
              ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
    pp_rec = (struct["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0]
              ["CommercialPropertyPersonalPropertyTable"]["CommercialPropertyPersonalProperty"][0])
    # The domain-legal CovType for this coverage, on the Personal Property
    # ITEM -- confirmed against DomainCovTypePrsnlProp.DomainTable.csv.
    # Nothing else needs to be submitted: `CommercialPropertyNonOwnedTrailers
    # EarthquakeCoverage` (and its four sibling Non-Owned Trailers forms) is
    # a SINGLETON the engine auto-instantiates once CovType is set, not a
    # submitted table entry -- confirmed by running (finding 5). A first
    # version of this script submitted a `...Table` collection entry with
    # its own `Limit=50000`, matching the field names in the rule XML; the
    # engine silently ignored it (the singleton it actually computes has no
    # such field at all) -- exactly the kind of submission-shape trap this
    # project has flagged before, now on a table/singleton distinction.
    pp_rec["CovType"] = "Non-Owned Trailers"
    return sub


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    book = book_for(JURIS, ASOF)
    print(f"{book}\n")

    threshold_table = book.parent_table("NonOwnedTrailersLimitThreshold")
    print(f"NonOwnedTrailersLimitThreshold, filed rows: {list(threshold_table.rows)}")
    assert len(threshold_table.rows) == 1 and threshold_table.rows[0][2] == LIMIT_THRESHOLD, (
        "filed threshold does not match the hand-read value -- re-check before predicting")

    c = chunk10_all.contents_predict(book)
    final_eq_rate = c["FinalEQRate"]
    premium = (final_eq_rate * ((Decimal(PARENT_LIMIT) - LIMIT_THRESHOLD) / 100)).quantize(Decimal("1"))
    print("\nHand-derivation, Non-Owned Trailers EQ coverage (plain branch):")
    print(f"  Contents' own FinalEQRate (shared, from C10-11)         = {final_eq_rate}")
    print(f"  LimitToUse = ../EQLimitToUse = Contents' own Limit       = {PARENT_LIMIT}"
          f"  (NOT this record's own Limit={RECORD_LIMIT} -- see finding 4)")
    print(f"  (LimitToUse-Threshold)/100 = ({PARENT_LIMIT}-{LIMIT_THRESHOLD})/100     = "
          f"{(Decimal(PARENT_LIMIT)-LIMIT_THRESHOLD)/100}")
    print(f"  Premium = round({final_eq_rate} x {(Decimal(PARENT_LIMIT)-LIMIT_THRESHOLD)/100}, 0) = {premium}\n")

    ip = Interpreter(book, rounding=ROUNDING, trace=a.trace,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", submission())
    ip.run(data)

    checks = [
        ("Contents FinalEQRate (shared)", PP + "/FinalEQRate", str(final_eq_rate)),
        ("Non-Owned Trailers LimitThreshold", NOT_ENDT + "/LimitThreshold", str(LIMIT_THRESHOLD)),
        ("Non-Owned Trailers LimitToUse", NOT_ENDT + "/LimitToUse", str(PARENT_LIMIT)),
        ("Non-Owned Trailers Premium", NOT_ENDT + "/Premium", str(premium)),
        ("Ordinary Contents BGI Premium (regression)", CONTENTS_BASIC_PREM, "223"),
    ]
    ok = True
    for label, path, want in checks:
        got = read(path, data)
        try:
            good = got is not None and Decimal(got) == Decimal(want)
        except Exception:
            good = got == want
        ok &= good
        flag = "" if good else f"   <-- expected {want}"
        print(f"  {label:44s} = {str(got):>10s}{flag}")

    if ip.messages:
        print(f"\n  ISO validation messages ({len(ip.messages)}): "
              + "; ".join(str(m)[:60] for m in ip.messages[:6]))

    print()
    if ok:
        print("MATCH -- Non-Owned Trailers' own EQ coverage reads Contents' "
              "already-computed FinalEQRate (a thin consumer, not its own "
              "rating engine) but genuinely gates on its OWN filed "
              "LimitThreshold subtraction before dividing by 100 -- "
              "confirmed by running, not just reading the XML. Verdict: "
              "neither wholly separate machinery nor a pure re-run -- a "
              "peer Contents coverage form with its own eligibility gate, "
              "reading a shared rate. No engine gap.")
        return 0
    print("MISMATCH above -- not patched here if it traces to engine code, "
          "per this project's standing rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
