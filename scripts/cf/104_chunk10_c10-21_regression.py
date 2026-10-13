"""The one-command regression -- chunks 0-17 and the General Liability suites.

Built for C10-21 (chunks 1-9 after chunk 10's _lookup_banded fix,
docs/CF-ENGINE-FIX-BANDED-LOOKUP.md). Extended 2026-09-22 (C11-24, part 1) to
cover chunk 10's own golden case and tests and chunk 11's, so "is everything
green?" is one command again -- before this, chunks 10 and 11 needed four
scripts run by hand after every engine change.

Three checks per script, not one:

  1. exit code 0                       -- the script's own assertions passed
  2. no failure marker in its output   -- MISMATCH / RAISED / Traceback /
                                          "<< expected", so a script that
                                          reports a disagreement without
                                          exiting non-zero is still caught
  3. every DOCUMENTED figure present   -- the dollar amounts docs/CF-START-HERE.md
                                          and the chunk golden-case docs record
                                          for that script, matched as standalone
                                          tokens in its output

Check 3 is the one that makes this a regression rather than a smoke test:
exit 0 only proves a script agreed with itself. Check 3 pins it to the number
written down before today. It can, in principle, pass on a coincidental token
match, which is why it is run ALONGSIDE checks 1 and 2 and not instead of them.

--selftest runs the harness against a deliberately wrong expectation and a
deliberately failing command, and fails if the harness reports them green --
this project's standing "a check that finds nothing needs its denominator
tested too" rule (CF-START-HERE.md).

Usage:
    python scripts/cf/104_chunk10_c10-21_regression.py
    python scripts/cf/104_chunk10_c10-21_regression.py --selftest
    python scripts/cf/104_chunk10_c10-21_regression.py --only 01 09 68
    python scripts/cf/104_chunk10_c10-21_regression.py --no-gl
    python scripts/cf/104_chunk10_c10-21_regression.py --quick           # after each RC
    python scripts/cf/104_chunk10_c10-21_regression.py --jobs 1          # the old serial run

Tiers (2026-09-30). FULL (default): everything, 6 scripts at a time (--jobs), with the six slow
exhaustive scripts running a deterministic sample of their grids (scripts/cf/_regress.py);
--gate runs those grids in full, at every chunk gate. After an engine change, run
206_snapshot_regression.py --check first (~4 min, every stored ISO payload re-rated). QUICK (--quick): every golden case with all its pinned
figures + the current chunk's own scripts, no GL, after each RC. Each script is its own
process either way; a numbered [i/n elapsed] line prints as each finishes, and the report
below it keeps the original order and format. The serial full run had grown to ~75 min.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CF = ROOT / "scripts" / "cf"
TESTS = ROOT / "tests"

FAILURE_MARKERS = ("MISMATCH", "RAISED", "Traceback", "<< expected")

# The zero-case scripts PREDICT raises -- the null-premium guard firing on an
# absent Limit is the finding, not a failure. "RAISED" is a legitimate word in
# their output, so it is dropped from their marker set and replaced by a
# positive requirement: each one must still print its own all-cases-match line.
# Found by running, not assumed: all three exit 0 and all three say so.
ZERO_CASE_MARKERS = ("MISMATCH", "Traceback", "<< expected")
ZERO_CASE_REQUIRE = ("match their derivation",)

#: The scripts the relaxation above was written for, BY NAME. It used to key on
#: "zero_cases" in the filename, which silently widened to chunk 10's and 11's
#: zero-case scripts -- neither prints "RAISED" nor the match-line, so the
#: substring rule would have failed them for the wrong reason. Found when
#: adding them (2026-09-22), not after a false red.
ZERO_CASE_SCRIPTS = {"42_chunk6_zero_cases.py", "51_chunk7_zero_cases.py",
                     "61_chunk8_zero_cases.py"}

# (script, chunk, what it holds, documented figures that must appear)
#
# Figures are transcribed from docs/CF-START-HERE.md's own golden-case table
# and, for chunk 9, from docs/CF-CHUNK9-GOLDEN-CASE.md. They are the numbers
# recorded BEFORE the engine fix -- that is the whole point of listing them
# here rather than reading them back out of a fresh run.
GOLDEN = [
    ("00_chunk0_checks.py", 0,
     "foundation: operators, resolver, edition chain", []),
    ("01_golden_case.py", 1,
     "Building Basic Group I", ["261", "263", "288"]),
    ("09_chunk2_golden_case.py", 2,
     "Building Basic Group II", ["261", "32"]),
    # CF-START-HERE.md records "16 / 54, layering on Basic to 293 / 309 / 347".
    # 293 is NOT printed by this script and its absence is not a regression:
    # 293 is the Basic-only subtotal (261 + 32), which is chunk 2's figure, not
    # chunk 3's. This script prints the two CUMULATIVE totals it is responsible
    # for -- 261+32+16=309 and 261+32+54=347. Checked by reading the script's
    # own output, not by dropping an inconvenient expectation.
    ("15_chunk3_golden_case.py", 3,
     "Building Broad and Special, layering on Basic",
     ["16", "54", "309", "347"]),
    ("22_chunk4_golden_case.py", 4,
     "Contents, four forms; Building unmoved",
     ["223", "24", "16", "137", "263", "32"]),
    ("32_chunk5_golden_case.py", 5,
     "Business Income, four forms; Building unmoved",
     ["112", "13", "23", "47", "261", "32"]),
    ("41_chunk6_golden_case.py", 6,
     "Special Class, four forms; Building unmoved",
     ["66", "209", "14", "44", "261", "32"]),
    ("50_chunk7_golden_case.py", 7,
     "Special Class Business Income; the item unmoved",
     ["39", "123", "23", "47", "66", "209"]),
    ("59_chunk8_golden_case.py", 8,
     "Legal Liability, Building and Contents",
     ["60", "7", "4", "12", "132", "15", "11", "93"]),
    ("68_chunk9_golden_case.py", 9,
     "Blanket rating, two dispersed structures", ["255", "510"]),
    # docs/CF-CHUNK10-GOLDEN-CASE.md: EQ premium $6, ordinary BGI unmoved $261.
    ("85_chunk10_golden_case.py", 10,
     "Earthquake, Building; ordinary premium unmoved", ["6", "261"]),
    # docs/CF-CHUNK11-GOLDEN-CASE.md: Tenants Lease $268 BGI + $30 BGII = $298.
    ("114_chunk11_golden_case.py", 11,
     "Leasehold Interest, Tenants Lease", ["268", "30", "298"]),
    # Chunk 12 (C12-41, 2026-09-23). Each figure was derived by hand and written
    # into the family's doc BEFORE its first run, and each matched ISO live.
    ("127_chunk12_golden_case.py", 12,
     "Debris Removal on chunk 2's building; building unmoved", ["49", "6", "55", "261", "32"]),
    ("130_chunk12_ordinance_golden_case.py", 12,
     "Ordinance or Law, A and B & C Separate", ["39", "5", "55", "7", "82", "10", "198"]),
    ("133_chunk12_utility_golden_case.py", 12,
     "Utility Services, direct damage and time element", ["15", "4", "9", "112"]),
    ("137_chunk12_drone_golden_case.py", 12,
     "Unmanned Aircraft on chunk 4's Special Contents", ["187", "137"]),
    ("139_chunk12_green_golden_case.py", 12,
     "Green Upgrades on chunk 2's building", ["27", "3", "30", "33", "261"]),
    ("141_chunk12_dependent_golden_case.py", 12,
     "Dependent Properties, Broad form on chunk 5's Business Income", ["80", "12", "112"]),
    # Chunk 15 (C15-20, 2026-09-25). One golden case per formula variant, each derived by
    # hand before the run and matched by ISO live: $1,013 (A, building credit), $1,066
    # (B, no credit), $1,065 (C, one rounding), $959 (contents / policy credit, C15-10).
    ("169_chunk15_rc2.py", 15,
     "manual-premium endorsements, one golden case per variant + all 23 on one policy",
     ["1013", "1066", "1065", "959"]),
    # Chunk 16 (C16-22, 2026-09-25). Each derived by hand before the run and matched by ISO live:
    # EPI $33, Pollutant Clean Up BGI $22 ($60 in G9b), Spoilage $513, IL $46, OK $960.
    ("175_chunk16_rc2.py", 16,
     "Business Income options, Pollutant Clean Up, Molten Material, Spoilage golden cases",
     ["33", "22", "60", "513", "46", "960"]),
    # Chunk 17 (C17-21, 2026-09-28). Each derived by hand before the run and matched by ISO live:
    # Landlord BGI $77 (L1), Off-Premises Collision $982 / OTC $343 (O1), SCBI Mining BGII $253 (M1),
    # SCBI Watercraft $13 (W1), payroll BI BGI $63 (P1).
    ("181_chunk17_rc2.py", 17,
     "Business Income add-ons: Landlord, payroll, power-heat, Mining, Watercraft, Off-Premises golden cases",
     ["77", "982", "343", "253", "13", "63"]),
    # Chunk 18 (C18-21, 2026-09-29). Each derived by hand before the run and matched by ISO live:
    # Agreed Value building BGI $10 (A1), blanketed $13 / $25 (A3), Functional Valuation $79 / $52 (F1),
    # Rebuilding building BGI $55 (R1), Vacancy Permit building / contents BGI $152 / $246 (V1).
    ("187_chunk18_rc2.py", 18,
     "valuation and condition modifiers: Agreed Value, Inflation Guard, Functional, Rebuilding, Vacancy, Peak Season",
     ["10", "13", "25", "79", "52", "55", "152", "246"]),
    # Chunk 19 (C19-22, 2026-09-29). Each derived by hand before the run and matched by ISO live: tenants' glass
    # BGI $122 (T1, no deductible) / $116 (T2, $250), the other-than-metal sign $193 (S1), Vermont trees BGII $64
    # (TR2, vehicle factor 1.15), Brands BGI $47 with the cap binding (B2), Leased $392 (L1), Temporarily Away
    # Special $24 (TA1, theft covered).
    ("192_chunk19_rc2.py", 19,
     "scheduled property items: Tenants', Antennas, Trees, Signs, Brands, Household, Leased, Temporarily Away, Manufacturers",
     ["122", "116", "193", "64", "47", "392", "24"]),
    # Chunk 20 (C20-24, 2026-09-29). Each derived by hand before the run and matched by ISO live: Fire Department
    # $85 / $173 through the location's higher limit (F1 / F2), Tobacco $23 at the band edge (TB1), Mortgageholders
    # $606 across all five layers (MG4), fungus $25 with the incremental 10 x (forms - 1) (FU2), blanket radioactive
    # $159 / $321 at the average rate (RA2), EB building $44 with the 250 deductible (EB2).
    ("200_chunk20_rc2.py", 20,
     "small coverages with their own tables: Fire Department, Tobacco, Mortgageholders, Fungus, Special COL, Radioactive, Pier, ACP, Food, EB",
     ["85", "173", "23", "606", "25", "159", "321", "44"]),
    # Chunk 21 (C21-19, 2026-09-30). Each derived by hand before the run and matched by ISO live: sewer building /
    # PP (borrowed factor) / special class / BI at 25,000 $167 / $164 / $17 (SW1), PP alone $170 (SW3), the limits case
    # $332 / $68 / $197 / $69 / $28 (SW4), loss assessment Over 10,000 = 25,000 with sub-limit 14,000 $26 (LA4), misc.
    # real property 50,000 with a 1,000 deductible $223 (MR2), FL condo building record $244 (one rounding, FC2),
    # FL SPP special class $293 (FC5: ours; ISO never attaches it, OI-116).
    ("208_chunk21_rc2.py", 21,
     "sewer backup, condo unit-owners options (loss assessment, misc. real property), FL commercial units in residential condos",
     ["167", "164", "17", "170", "332", "68", "197", "69", "28", "26", "223", "244", "293"]),
    # Chunk 22 (C22-22, 2026-10-01). Each derived by hand before the run and matched by ISO live: Value Reporting "Not Used"
    # Group I $146 / $565 and Special $247 at each row's own rate on 0.75 x Limit (V1), General Information $183 (V1) /
    # $481 with acquired 60,000 (G1) / $189 at exactly 50,000 (G2), blanketed Group I $597 (B1), Additional Locations
    # Provisions Group I $348 / $174 at 90% (A1) and $267 on three locations (A2).
    ("215_chunk22_rc2.py", 22,
     "multi-location: Value Reporting Form (Not Used, blanketed, General Information) and Additional Locations Special Coinsurance",
     ["146", "565", "247", "183", "481", "189", "597", "348", "174", "267"]),
    # Chunk 23 (C23-20, 2026-10-01). Each derived by hand before the run and matched by ISO live (RC-2): MA heating-oil
    # remediation $241 (3 tanks + 2 buildings) / $67 (1 tank), its Pollutant Clean Up credit -$17 at the cap / -$9 under it,
    # tenant relocation $16 (6 units) / $30 (over the cap); AK attorneys' fees $12 / $8 / $11; CA Limited EQ $80 / $24 / $21
    # and Additional EQ $1,235; VA broad form Cov B Group I $591, Cov C Group I $886.
    ("220_chunk23_rc2.py", 23,
     "state-only families: MA heating oil and tenant relocation, AK attorneys' fees, CA Limited / Additional EQ, VA Ordinance or Law",
     ["241", "67", "-17", "-9", "16", "30", "12", "8", "11", "80", "24", "21", "1235", "591", "886"]),
    # Chunk 24 (C24-23, 2026-10-01). Each derived by hand before the run (container rates too) and matched by ISO live (RC-2):
    # reporting form 400,000 Group I $164, II $321, Special $94, Broad $78, EQ $20; renovations Frame Group I $454, Fire
    # Resistive $270, beside a reporting form Special $145; collapse $8 / $187 / $235; materials of others $232; the stored theft
    # fixture at 120,000 $11; premium adjustment Group I $36 / $48.
    ("225_chunk24_rc2.py", 24,
     "Builders Risk: reporting form, renovations, premium adjustment, collapse, theft, materials of others, CP 10 44, EQ",
     ["164", "321", "94", "78", "20", "454", "270", "145", "8", "187", "235", "232", "11", "36", "48"]),
    # Chunk 25 (C25-24, 2026-10-02). Each derived by hand before the run and matched by ISO live (RC-2): building $493 (table 3,
    # CRS 5), $616 (no CRS), $36 (deductible 500), $5,758 (100,000); contents $799, $643 (deductible 25,000); special class $460;
    # BI $343, combined types $403 / $286, maximum period $716, SCBI extra expense only $1,059; OI-122 as written $531;
    # blankets $1,273 / $1,731 / $1,952 / excess $7,644; excess contents $8,534.
    ("230_chunk25_rc2.py", 25,
     "Flood: building / contents / special class / BI / SCBI, the seven rate-modification tables, CRS, blankets, excess over NFIP",
     ["493", "616", "36", "5758", "799", "643", "460", "343", "403", "286", "716", "1059", "531", "1273", "1731", "1952", "7644", "8534"]),
    # Chunk 26 (C26-21, 2026-10-02). Each derived by hand before the run and matched by ISO live (RC-2): Specific building Group I
    # $362, contents on their own rate $150 / $335, BI on the building's $137; SC Specific Group II $67 / $37 / $24; CA One-Term
    # building $354, contents $146, BI $538 at rate 1.0 (OI-124).
    ("235_chunk26_rc2.py", 26,
     "Specific and Tentative rating: building / contents / BI Group I, Specific Group II at the hazard thresholds, CA One-Term",
     ["362", "150", "335", "137", "67", "37", "24", "354", "146", "538"]),
]

# The machinery each chunk added -- run whenever shared code changes, which is
# exactly what happened today. No figure list: these assert internally and are
# held to checks 1 and 2.
MACHINERY = [
    ("04_shared_names.py", "gate point 6 across all chains"),
    ("05_exclusion_records.py", "gate point 7 census"),
    ("21_chunk3_special_structure.py", "chunk 3 Special structure"),
    ("23_chunk4_foreach.py", "chunk 4 repeating group"),
    ("35_chunk5_factor.py", "chunk 5 SetFactor -- selection, not multiplication"),
    ("39_chunk5_crossform.py", "chunk 5 three coverages, none moving"),
    ("42_chunk6_zero_cases.py", "chunk 6 zero cases"),
    ("45_chunk6_description_chain.py", "chunk 6 description chain"),
    ("46_chunk6_perform.py", "chunk 6 per-form specifics"),
    ("47_chunk6_forms.py", "chunk 6 form claims"),
    ("48_chunk6_crossform.py", "chunk 6 cross-form claims"),
    ("51_chunk7_zero_cases.py", "chunk 7 zero cases"),
    ("54_chunk7_borrowed.py", "chunk 7 borrowed rate"),
    ("55_chunk7_perform.py", "chunk 7 per-form specifics"),
    ("56_chunk7_crossform.py", "chunk 7 cross-form claims"),
    ("57_chunk7_open_questions.py", "chunk 7 open questions"),
    ("61_chunk8_zero_cases.py", "chunk 8 zero cases"),
    ("64_chunk8_fork.py", "chunk 8 fork"),
    ("65_chunk8_map.py", "chunk 8 traced map"),
    ("66_chunk8_crossform.py", "chunk 8 map scored, cross-coverage LOI leak"),
    ("69_chunk9_c9-02_chain_trace.py", "chunk 9 blanket chain trace"),
    ("72_chunk9_c9-06_three_gates.py", "chunk 9 three gates"),
    ("75_chunk9_c9-09_setnoneq_diff.py", "chunk 9 SetNonEQBlanketValues diff"),
    ("80_chunk9_c9-15-16-17_reachability.py", "chunk 9 reachability"),
    ("83_chunk9_c9-20_crosscoverage_leak.py", "chunk 9 cross-coverage leak"),
    # Chunk 10 -- the scripts that assert (exit 1 on disagreement). Its
    # censuses (84/86/87/89/90/92/93/94/97/102) always exit 0 and are listed
    # under EXCLUDED rather than run for show.
    ("88_chunk10_c10-04_zero_cases.py", "chunk 10 zero cases, two tiers"),
    ("91_chunk10_c10-09_message_tally.py", "chunk 10 message tally"),
    ("95_chunk10_c10-11_all_groups_chain.py", "chunk 10 EQ chain, all 5 groups"),
    ("96_chunk10_c10-12_eqclass_eqterr_live.py", "chunk 10 EQClass/EQTerr live"),
    ("98_chunk10_c10-14_ordinary_chain_separation.py", "chunk 10 EQ vs ordinary chain"),
    ("99_chunk10_c10-16_legal_liability_eq.py", "chunk 10 Legal Liability EQ"),
    ("100_chunk10_c10-15_blanket_reachability.py", "chunk 10 EQ blanket branch"),
    ("101_chunk10_c10-17_non_owned_trailers.py", "chunk 10 Non-Owned Trailers EQ"),
    ("103_chunk10_c10-19_sublimit_flatdeductible.py", "chunk 10 sub-limit (banded-lookup fix)"),
    ("105_chunk10_c10-20_fixture_sample.py", "chunk 10 fixture census, 364 CF payloads"),
    # Chunk 11.
    ("115_chunk11_groupA_annuity.py", "chunk 11 annuity, injection, live inputs"),
    ("116_chunk11_groupB_subcoverages.py", "chunk 11 four sub-coverages"),
    ("117_chunk11_c11-04_zero_cases.py", "chunk 11 zero cases, seven tiers"),
    ("119_chunk11_groupD_shared_machinery.py", "chunk 11 shared machinery"),
    ("120_chunk11_groupsEF_inventory_states.py",
     "chunk 11 inventory, states (46), DateDifference sign pinned (OI-107)"),
    # Chunk 12.
    ("125_chunk12_c12-03_operand_types.py",
     "chunk 12 operand types + 17 fixtures + the OI-108 blanket-drone probe"),
    ("128_chunk12_debris_removal_gates.py", "chunk 12 Debris Removal gates 2-8"),
    ("131_chunk12_ordinance_gates.py", "chunk 12 Ordinance or Law gates 2-8"),
    ("134_chunk12_utility_gates.py", "chunk 12 Utility Services gates 2-8"),
    ("138_chunk12_drone_gates.py", "chunk 12 Unmanned Aircraft gates 2-9"),
    ("140_chunk12_green_gates.py", "chunk 12 Green Upgrades gates 2-8"),
    ("142_chunk12_dependent_gates.py", "chunk 12 Dependent Properties gates 2-8"),
    ("121_chunk11_c11-09_messages.py",
     "chunk 11 messages: golden registered; ours == ISO's saved responses"),
    # Chunk 13 (2026-09-24). No network: 145 replays ISO's own stored responses.
    ("144_chunk13_c13-02_rule_order.py", "chunk 13 terrorism rule order and roll-up, 5 editions"),
    ("145_chunk13_c13-03_replay.py",
     "chunk 13 14 stored ISO terrorism responses, field by field (OI-111 pinned: CA $153)"),
    ("147_chunk13_c13-04_operand_types.py", "chunk 13 operand types; all four TRIA stages live, timeline by hand"),
    ("148_chunk13_c13-05_attach_map.py", "chunk 13 attach map: 168 answer combinations x attach/delete"),
    ("149_chunk13_golden_case.py", "chunk 13 golden case OR $8 + 4 variants (fire exception, TRIA proration), 38 figures"),
    ("150_chunk13_c13-08-09_groups_rollup.py", "chunk 13 other four groups + roll-ups, 9 policies, 53 figures"),
    ("151_chunk13_rc3_mechanisms.py", "chunk 13 RC-3: timeline, five form families, sub-limit, zeros, override, literals (36 cases)"),
    ("152_chunk13_rc4_states.py", "chunk 13 RC-4: 46 states, every tier, own rows + rules (290 cases)"),
    ("154_chunk13_rc5_fields_messages.py",
     "chunk 13 every terrorism field + messages vs 293 stored ISO responses (offline)"),
    # Chunk 14 (2026-09-24). Offline: both re-rate stored ISO responses.
    # 157_ runs its fixed 46-fixture covering sample here (~45 s); `--all` (293, ~4 min)
    # runs at every chunk close-out and edition change (user-approved 2026-09-24).
    ("157_chunk14_c14-02_total_replay.py", "chunk 14 every premium + the policy total, 46-fixture covering sample"),
    ("158_chunk14_rc1_scope_machinery.py",
     "chunk 14 RC-1: no minimum premium, state overrides only add records, negative premiums count"),
    ("159_chunk14_rc2_total.py", "chunk 14 RC-2: golden total $1,193, what counts, several locations, rounding"),
    ("160_chunk14_rc3_modifiers.py", "chunk 14 RC-3: IRPM (OR + 5 states), package mod, multi-premium, Standard Property Policy"),
    ("161_chunk14_c14-16_statcode_replay.py", "chunk 14 RC-4: every stat value vs stored ISO responses, strict, 46-fixture sample"),
    ("162_chunk14_rc4_state_statcodes.py", "chunk 14 RC-4: state earthquake stat codes (FL own classes, TX, OR)"),
    ("163_chunk14_c14-19_zero_cases.py", "chunk 14 RC-5: every 0 / blank modifier against its branch; the 1..199 stat-code bound"),
    ("164_chunk14_c14-18_all_states.py", "chunk 14 RC-5: IRPM and Standard Property Policy in all 46 states"),
    ("165_chunk14_c14-20_shared_modifiers.py", "chunk 14 RC-5: modifier fields by path on every record vs stored ISO, sample"),
    # Chunk 15 (2026-09-25). Engine-only runs (no --live); 172_ is offline against stored responses.
    ("168_chunk15_rc1.py", "chunk 15 RC-1: attach map, every modifier path resolved, engine = hand on 29 records"),
    ("170_chunk15_rc3.py", "chunk 15 RC-3: 22 zero / exclusion / message cases as derived; shared names"),
    ("171_chunk15_rc4.py", "chunk 15 RC-4: all 23 records in all 46 states + VA 2021 (tree check), as derived"),
    ("172_chunk15_c15-19_downstream.py", "chunk 15 RC-5: total moves by the endorsements; stat fields vs stored ISO"),    # Chunk 16 (2026-09-25). Engine-only runs (no --live); 177_ on its default sample; 178_ offline.
    ("174_chunk16_rc1.py", "chunk 16 RC-1: attach map, every record priced by the hand evaluator"),
    ("176_chunk16_rc3.py", "chunk 16 RC-3: zero / message / exclusion cases as derived; shared names"),
    ("177_chunk16_rc4.py", "chunk 16 RC-4: every family in the sample states + probes, as derived"),
    ("178_chunk16_c16-21_downstream.py", "chunk 16 RC-5: total moves by the families (T1, T2); stat values vs stored ISO"),
    # Chunk 17 (2026-09-28). Engine-only runs (no --live); 183_ on its default sample + probes; 184_ offline.
    ("180_chunk17_rc1.py", "chunk 17 RC-1: $0 fixtures explained, switches flipped, hand = engine on 26 records"),
    ("182_chunk17_rc3.py", "chunk 17 RC-3: 30 zero / message / name / exclusion cases as derived"),
    ("183_chunk17_rc4.py", "chunk 17 RC-4: every family in the sample states + 10 probes, as derived"),
    ("184_chunk17_c17-20_downstream.py", "chunk 17 RC-5: total moves by the families (T1 $1,969, T2 $2,643); stat values vs stored ISO"),
    # Chunk 18 (2026-09-29). Engine-only runs (no --live); 189_ on its default sample + probes; 190_ offline.
    ("186_chunk18_rc1.py", "chunk 18 RC-1: $0 fixtures explained, switches flipped, hand = engine on 53 records"),
    ("188_chunk18_rc3.py", "chunk 18 RC-3: zero / message / name / exclusion cases as derived"),
    ("189_chunk18_rc4.py", "chunk 18 RC-4: every family in the sample states + 4 SPP probes, as derived"),
    ("190_chunk18_c18-20_downstream.py", "chunk 18 RC-5: total moves by the families (T1 $2,520, T2 $2,554, blanket $38); stat values vs stored ISO"),
    # Chunk 19 (2026-09-29). Engine-only runs (no --live); 196_ on its default states + probes; 198_ offline.
    ("191_chunk19_rc1.py", "chunk 19 RC-1: stored tenants' records, switches, 63 records hand = engine, tables"),
    ("193_chunk19_rc3.py", "chunk 19 RC-3: 27 zero / message cases + the Manufacturers refusal probe, as derived"),
    ("194_chunk19_c19-15-16.py", "chunk 19 RC-3: shared names (submitted values) and exclusion records, as derived"),
    ("195_chunk19_c19-17_eq_tiers.py", "chunk 19 RC-4: the EQ sub-limit tier layer, every factor independent"),
    ("196_chunk19_c19-18_states.py", "chunk 19 RC-4: the state rewrites, FL / MT glass, the plan probes, as derived"),
    ("197_chunk19_c19-19_editions.py", "chunk 19 RC-4: every rule diffed per edition; MO / NC / MA probes"),
    ("198_chunk19_c19-21_downstream.py", "chunk 19 RC-5: total +$1,941 / +$14,054 incl. the contents' LOI move; stat values vs stored ISO"),
    # Chunk 20 (2026-09-29). Engine-only runs (no --live); 199_ without the stored re-rate; 203_ on a small state
    # sample (the all-states run needs batches: memory); 204_ offline.
    ("199_chunk20_rc1.py --skip-stored", "chunk 20 RC-1: switches flipped, 28 records hand = engine on four trees + a blanket, tables"),
    ("201_chunk20_rc3.py", "chunk 20 RC-3: 12 zero + 50 message cases by level, as derived (OI-115 cases pinned)"),
    ("202_chunk20_c20-17-18.py", "chunk 20 RC-3: shared names (submitted values) and the cyber factors, as derived"),
    ("203_chunk20_rc4.py --no-editions --runs OR,AL,FL,NY,VA,MO,NC,P-pip-AL,P-FL-fd,P-VA-vol,E-FD-MA,E-FU-MO,E-MO",
     "chunk 20 RC-4: a state sample, the rewrite and edition probes, as derived"),
    ("204_chunk20_c20-23_downstream.py", "chunk 20 RC-5: total +$977 / +$5,110; blanket roll-up moves only on radioactive"),
    # Chunk 21 (2026-09-30). Engine-only runs (no --live): each asserts its own predictions and exits 1 on any miss.
    ("207_chunk21_rc1.py", "chunk 21 RC-1: switches flipped, borrowed values and loss assessment by hand (66 cases), tables, 46 states"),
    ("209_chunk21_c21-10-11.py", "chunk 21 RC-3: 11 zero cases + 39 message cases, as derived (OI-103 / OI-117 refusals pinned)"),
    ("210_chunk21_c21-12-13.py", "chunk 21 RC-3: shared names (submitted values), no cyber, the options container's stat codes"),
    ("211_chunk21_c21-14-17.py", "chunk 21 RC-4: the state rewrites, FL sewer, MO's edition caps, all 46 states, state-aware"),
    ("212_chunk21_c21-18_downstream.py", "chunk 21 RC-5: total +$651 / +$6,405; terrorism untouched"),
    # Chunk 22 (2026-10-01). Engine-only runs (no --live); 217_ samples its cases (the 46-state run needs batches: memory).
    ("213_chunk22_rc1.py", "chunk 22 RC-1: MLAR write order, built touchpoints, attach and switches, GI by hand, tables (OI-119 pinned)"),
    ("216_chunk22_rc3.py", "chunk 22 RC-3: 10 zero cases, 24 message cases by level, 4 shared names, 5 exclusion probes, as derived"),
    ("217_chunk22_rc4.py --cases T-AL1,T-AR,T-CA1,E1,E2,E3,E3b,E5,SC1,S-OR,S-FL,S-MO",
     "chunk 22 RC-4: the state rewrites, MO V02's edition differences, 8-location rounding, a state sample, as derived"),
    ("218_chunk22_c22-21_downstream.py", "chunk 22 RC-5: total +$38 / -$622 / +$1,991 / -$3,878; contents switched off, terrorism on 0.75 x Limit"),
    # Chunk 23 (2026-10-01). Engine-only runs (no --live); 222_ samples its fuller policies (the full run re-runs 904_).
    ("219_chunk23_rc1.py", "chunk 23 RC-1: every record of the four states' families hand = evaluator = engine; switches, tables, editions"),
    ("221_chunk23_rc3.py", "chunk 23 RC-3: 43 zero / message / shared-name / exclusion cases, as derived"),
    ("222_chunk23_rc4.py --cases F-MA,F-AK,F-CA,F-VA", "chunk 23 RC-4: fuller state policies (the old-package probes print RAISED by design, OI-120: run them directly)"),
    ("223_chunk23_c23-19_downstream.py", "chunk 23 RC-5: total + $192 / $31 / $806 / $3,908 (fuller) and $234 / $31 / $1,360 / $3,902 (golden); nothing else moves"),
    # Chunk 24 (2026-10-01). Engine-only runs (no --live). 224_ re-rates all 293 stored responses (~4 min).
    ("224_chunk24_rc1.py", "chunk 24 RC-1: the stored evidence (293 unchanged, BR theft on 145), every record hand = evaluator = engine, OI-121"),
    ("226_chunk24_rc3.py", "chunk 24 RC-3: 48 zero / message / shared-name / exclusion cases, as derived"),
    ("227_chunk24_rc4.py", "chunk 24 RC-4: the 16 rewriting states (own rule text), the edition probe, the built readers"),
    ("228_chunk24_c24-22_downstream.py", "chunk 24 RC-5: total + $1,976 / $13,199 / $1,982 / $1,861; nothing else moves"),
    # Chunk 25 (2026-10-02). Engine-only runs (no --live). 229_ re-rates all 293 stored responses (~4 min); 232_ runs its 29
    # probes (editions, WV, Off-Premises, AK / FL blanks; the 46 state policies run with --states, in batches).
    ("229_chunk25_rc1.py", "chunk 25 RC-1: stored AK flood (manual), every flood record and intermediate value hand = evaluator = engine, tables"),
    ("231_chunk25_rc3.py", "chunk 25 RC-3: 41 zero / message / shared-name / exclusion cases, all 45 flood message rules, as derived"),
    ("232_chunk25_rc4.py", "chunk 25 RC-4: MO V02 / V03 / V04 edition probes, WV CP 10 68 and O&L flood, Off-Premises flood factor, AK / FL"),
    ("233_chunk25_c25-23_downstream.py", "chunk 25 RC-5: total + $3,521 / $3,277 / $10,522 / $3,116 / $22,828; nothing else moves"),
    # Chunk 26 (2026-10-02). Engine-only runs (no --live). 234_ replays the 126 distinct stored Specific / Tentative policies
    # against their stored ISO responses (~4 min: the regression check C26-21 asks for); 237_ runs the two MO edition probes
    # (the 46 state policies run with --states, in batches).
    ("234_chunk26_rc1.py", "chunk 26 RC-1: 126 stored Specific / Tentative policies = ISO, branch map, contents / BI rates, Group II, domains"),
    ("236_chunk26_rc3.py", "chunk 26 RC-3: 23 zero / message / shared-name / class-only cases, as derived (OI-125 pinned)"),
    ("237_chunk26_rc4.py", "chunk 26 RC-4: MO (V02) edition probes: no roof factor, BI on the building's final rate"),
    ("238_chunk26_c26-20_downstream.py", "chunk 26 RC-5: total + $56 / $701 / $68 / -$149 / -$794 Class -> Specific; nothing else moves"),
    ("239_chunk27_rc2.py", "chunk 27 RC-2: chunks 1-8 golden cases, every message in the register (M-001..M-006)"),
    ("240_chunk27_rc3.py", "chunk 27 RC-3: CA / FL Legal Liability, TX wind / hail, DC IL NY BCEG, MT NY Group II symbol, as predicted"),
    ("241_chunk27_rc4.py", "chunk 27 RC-4: theft exclusion on the drone / Dependent Properties; FL and WV Ordinance or Law, as predicted"),
    # Chunk 28 (registered at its gate, C28-22): the offline tests that can fail. The measurements (245_-247_, 249_,
    # 251_-256_) always exit 0 or replay every stored request; their findings are pinned by 206_'s snapshot.
    ("248_chunk28_c28-06_probes.py", "chunk 28 C28-06: 17 refusal probes refuse at the table ISO named (P5 / P9 built as written)"),
    ("250_chunk28_c28-07_oi123_probe.py", "chunk 28 C28-07: the OI-123 probe, as predicted"),
    ("257_chunk28_c28-19_older_package.py", "chunk 28 C28-19: a known-older package refuses, nothing else; 276 recorded state-dates"),
    # Sync checks (2026-10-01, user: "always in sync"). The deployed page is checked each turn by the Stop hook.
    ("check_status_docs.py --no-deployed", "status docs agree: task lists vs CF-BUILD-STATUS.html RC labels, tags, plan rows, START-HERE"),
    ("check_premium_census.py", "every in-force premium writer is a SetPremium rule (selftest: AK 2020's ErcRate writers are seen)"),
]

# Excluded on purpose, each with a reason -- no silent narrowing of scope.
EXCLUDED = [
    ("02/10/16/25/33 zero-case + 03/11/17/24/34/43/52/62 sweep scripts",
     "the state sweeps take minutes each and enumerate 47 jurisdictions; "
     "they were re-run green on 2026-09-18 and touch no banded lookup. "
     "Run them directly when a state-layer change lands."),
    ("chunk 10 censuses 84/86/87/89/90/92/93/94/97/102, chunk 11 census 106, "
     "chunk 12 censuses 123/124/126, chunk 13-17 censuses 143/156/166/167/173/179",
     "each states 'always exits 0 -- a census, not a test'; running them "
     "here would add minutes and prove only that they still print."),
    ("06/19/44/53/63/79/118/122 RaaS scripts, and chunk 12's 129/132/135/136",
     "they call ISO's live service; a regression of OUR engine must not "
     "depend on a network round trip. 63_chunk8_raas.py additionally exits "
     "non-zero BY DESIGN (OI-99)."),
    ("07_diagnose_message.py",
     "requires CLI arguments; a bare invocation is an argparse usage error."),
    ("the *_r1..r8 / *_m1 / *_t1 Excel-COM scripts",
     "a separate rater-streamlining workstream that drives Excel over COM. "
     "Not part of this engine's test surface, and RULE #0 applies."),
]


#: Environment for every script. The regular FULL run sets CF_REGRESSION_SAMPLE=1 so the slow exhaustive
#: scripts (scripts/cf/_regress.py) run a deterministic sample of their grids; --gate clears it.
ENV = dict(os.environ)


def run(cmd, cwd):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ENV)
    return p.returncode, (p.stdout or "") + (p.stderr or ""), time.time() - t0


def check(rc, out, figures, markers=FAILURE_MARKERS, require=()):
    """Return (ok, list of reasons it failed)."""
    bad = []
    if rc != 0:
        bad.append(f"exit {rc}")
    hit = [m for m in markers if m in out]
    if hit:
        bad.append("output carries " + "/".join(hit))
    missing = [f for f in figures
               if not re.search(rf"(?<![\d.]){re.escape(f)}(?![\d.])", out)]
    if missing:
        bad.append("documented figure(s) absent: " + ", ".join(missing))
    absent = [p for p in require if p not in out]
    if absent:
        bad.append("required phrase(s) absent: " + "; ".join(absent))
    return (not bad), bad


def selftest():
    """Prove the harness can fail. Three planted defects, all must be caught."""
    print("SELFTEST -- planting three defects the harness must catch\n")
    ok = True

    rc, out, _ = run([sys.executable, "-c", "raise SystemExit(3)"], ROOT)
    good, why = check(rc, out, [])
    print(f"  1. non-zero exit          -> caught={not good}  {why}")
    ok &= not good

    rc, out, _ = run([sys.executable, "-c", "print('PREMIUM MISMATCH')"], ROOT)
    good, why = check(rc, out, [])
    print(f"  2. MISMATCH in output     -> caught={not good}  {why}")
    ok &= not good

    rc, out, _ = run([sys.executable, "-c", "print('premium = 999')"], ROOT)
    good, why = check(rc, out, ["261"])
    print(f"  3. documented figure gone -> caught={not good}  {why}")
    ok &= not good

    # And the inverse: a clean run must pass, or the harness is just a
    # red-light generator.
    rc, out, _ = run([sys.executable, "-c", "print('premium = 261 OK')"], ROOT)
    good, why = check(rc, out, ["261"])
    print(f"  4. clean run              -> passes={good}  {why}")
    ok &= good

    # Token boundary: 261 must not be satisfied by 1261 or 261.5
    rc, out, _ = run([sys.executable, "-c", "print('1261 and 261.5')"], ROOT)
    good, _ = check(rc, out, ["261"])
    print(f"  5. no substring false pass-> caught={not good}")
    ok &= not good

    # The zero-case relaxation must not become a blanket amnesty: dropping
    # "RAISED" from the marker set is only safe because the match-line is
    # required in its place. Prove the replacement actually bites.
    rc, out, _ = run([sys.executable, "-c", "print('case 1 RAISED InterpretError')"], ROOT)
    good, why = check(rc, out, [], markers=ZERO_CASE_MARKERS,
                      require=ZERO_CASE_REQUIRE)
    print(f"  6. zero-case w/o match-line -> caught={not good}  {why}")
    ok &= not good

    rc, out, _ = run([sys.executable, "-c",
                      "print('case 1 RAISED\\nAll 7 cases match their derivation.')"], ROOT)
    good, why = check(rc, out, [], markers=ZERO_CASE_MARKERS,
                      require=ZERO_CASE_REQUIRE)
    print(f"  7. zero-case w/ match-line  -> passes={good}  {why}")
    ok &= good

    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def jobs_for(a):
    """every script this run covers, in report order: (section, name, cmd, figures, markers, require, label)."""
    def wanted(name):
        return a.only is None or any(name.startswith(p) for p in a.only)

    current = max(c for _, c, _, _ in GOLDEN)
    quick_chunk = a.chunk if a.chunk is not None else current
    jobs = []
    for script, chunk, what, figures in GOLDEN:
        if wanted(script):
            jobs.append(("golden", script, [sys.executable, "-u", f"scripts/cf/{script}"], figures,
                         FAILURE_MARKERS, (), (chunk, what)))
    for script, what in MACHINERY:
        if not wanted(script):
            continue
        # quick tier: every golden case (all pinned figures) + the current chunk's own scripts
        if a.quick and not what.startswith(f"chunk {quick_chunk} "):
            continue
        zero = script in ZERO_CASE_SCRIPTS
        # an entry may carry arguments after the script name (chunk 20: "199_... --skip-stored")
        name, *args = script.split()
        jobs.append(("machinery", script, [sys.executable, "-u", f"scripts/cf/{name}", *args], [],
                     ZERO_CASE_MARKERS if zero else FAILURE_MARKERS,
                     ZERO_CASE_REQUIRE if zero else (), (zero, what)))
    if not a.no_gl and not a.quick:
        for t in sorted(TESTS.glob("verify_*.py")):
            if wanted(t.name):
                jobs.append(("gl", t.name, [sys.executable, "-u", f"tests/{t.name}"], [],
                             FAILURE_MARKERS, (), None))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--only", nargs="*", default=None,
                    help="run only scripts whose filename starts with these")
    ap.add_argument("--no-gl", action="store_true",
                    help="skip the 16 General Liability suites")
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("ERC_MAX_WORKERS", "2")),
                    help="scripts run at once (default ERC_MAX_WORKERS, 2). Each script is its own process, "
                         "180-470 MB measured 2026-09-30 and more since; 6 at once crashed the 16 GB dev "
                         "machine as the suites grew (2026-10-13)")
    ap.add_argument("--gate", action="store_true",
                    help="chunk gate: the slow exhaustive scripts run their FULL grids (no sampling). "
                         "Without it they run a deterministic sample (scripts/cf/_regress.py)")
    ap.add_argument("--quick", action="store_true",
                    help="quick tier: every golden case (all pinned figures) + the current chunk's own "
                         "scripts, no GL -- after each RC. The full run is for gates and engine changes")
    ap.add_argument("--chunk", type=int, default=None,
                    help="with --quick: which chunk's scripts (default: the newest golden case's chunk)")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    jobs = jobs_for(a)
    if a.gate:
        ENV.pop("CF_REGRESSION_SAMPLE", None)
    else:
        ENV["CF_REGRESSION_SAMPLE"] = "1"
    tier = ("QUICK tier" if a.quick else "FULL run") + (", gate: full grids" if a.gate else ", slow grids sampled")
    print(f"Regression -- chunks 0-{max(c for _, c, _, _ in GOLDEN)} and the General Liability suites "
          f"({tier}, {len(jobs)} scripts, {a.jobs} at a time)")
    print("=" * 78)

    # run: each script its own process, a.jobs at once; a progress line as each finishes
    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        futs = {pool.submit(run, cmd, ROOT): name for _, name, cmd, *_ in jobs}
        for k, fut in enumerate(as_completed(futs), 1):
            name = futs[fut]
            rc, out, secs = fut.result()
            job = next(j for j in jobs if j[1] == name)
            good, why = check(rc, out, job[3], markers=job[4], require=job[5])
            results[name] = (good, why, out, secs)
            m, sec = divmod(int(time.time() - t0), 60)
            print(f"[{k}/{len(jobs)}  {m}m{sec:02d}s] {'OK ' if good else 'FAIL'} {name} ({secs:.0f}s)"
                  + ("".join(f"\n      !! {w}" for w in why) if not good else ""), flush=True)

    # report, in the original order and format
    failures = []
    sections = [("golden", "\nGOLDEN CASES -- exit code, failure markers, and documented figures"),
                ("machinery", "\nMACHINERY -- exit code and failure markers"),
                ("gl", "\nGENERAL LIABILITY -- the regression net for shared-code changes")]
    for sec_key, title in sections:
        sec_jobs = [j for j in jobs if j[0] == sec_key]
        if not sec_jobs:
            continue
        print(title)
        print("-" * 78)
        for _, name, _, figures, _, _, extra in sec_jobs:
            good, why, out, secs = results[name]
            if sec_key == "golden":
                chunk, what = extra
                fig = " ".join(f"${f}" for f in figures) or "(no dollar figure)"
                print(f"  chunk {chunk}  {name:38s} {'OK ' if good else 'FAIL'} {secs:5.1f}s  {fig}")
                print(f"            {what}")
            elif sec_key == "machinery":
                zero, what = extra
                tag = "  [zero-case: predicted raises allowed, match-line required]" if zero else ""
                print(f"  {name:42s} {'OK ' if good else 'FAIL'} {secs:5.1f}s  {what}{tag}")
            else:
                print(f"  {name:42s} {'OK ' if good else 'FAIL'} {secs:5.1f}s")
            if not good:
                failures.append((name, why, out))
                for w in why:
                    print(f"      !! {w}")

    print("\nOUT OF SCOPE, stated rather than silently dropped")
    print("-" * 78)
    for what, why in EXCLUDED:
        print(f"  - {what}\n      {why}")
    if a.quick:
        print("  - QUICK tier: the other chunks' machinery scripts and the GL suites (run the full "
              "regression at a gate or after an engine change)")

    m, sec = divmod(int(time.time() - t0), 60)
    print("\n" + "=" * 78)
    if failures:
        print(f"REGRESSION FAILED -- {len(failures)} script(s)  ({m}m{sec:02d}s)\n")
        for script, why, out in failures:
            print(f"--- {script}: {'; '.join(why)}")
            print("\n".join(out.strip().splitlines()[-15:]))
            print()
        return 1
    print(f"REGRESSION CLEAN ({tier}, {len(jobs)} scripts, {m}m{sec:02d}s) -- every golden case reproduces its "
          "documented figures,\nevery machinery script and every GL suite run exits 0 with no failure marker.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
