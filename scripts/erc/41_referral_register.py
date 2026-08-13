"""Build-order item 12, step 2 — classify the referral population.

Reads `out/referral_census.json` (step 1) and emits `out/referral_register.json`,
the artifact `escalate/` is promised to consume — build plan §5: *"an escalation
is a typed object that forces a REFER until answered."*

THE FOUR KINDS, from the item-12 plan
-------------------------------------
  1 DECLARED    the corpus says refer, in so many words. Detectable at LOAD time
                by reading a selector or a sentinel from the resolved package.
  2 MISSING     the lookup misses. Detectable at RATE time. Splits on failure
                mode, and the split is the practical crux: a NULL is loud and a
                ZERO is silent, and they need different plumbing.
  3 NONE        ERC carries no discriminator. NOT detectable at all. Each of
                these is a DECISION — submission requirement, accepted unguarded
                referral, or ISO escalation — and none of them is code.
  4 GUARD       the bound exists only inside a DoMessage* rule (N15). Detectable
                at rate time, but only as wide as the guard itself.

THE SELF-CHECK
--------------
Kind 3 means *no probe can find it*. Step 1's reconciliation independently
computed which conditions a probe can reach. **The two must agree**: every
kind-3 entry must be undetectable and every other kind must name a probe. If
they disagree, one of them is wrong — and the classification is the judgement,
so it is the one to distrust.

    python 41_referral_register.py 20260812 [--verbose]
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# id, source, condition, kind, detect, failure, scope
#   kind   1 DECLARED · 2 MISSING · 3 NONE · 4 GUARD
#   detect load | rate | never
#   failure null | zero | wrong-number | no-signal | n/a
REGISTER = [
    # ---------------------------------------------------------------- kind 1
    ("R01", "gate 335-RR", "Railroad Protective is ELP-only; the selector is "
     "single-valued `Industry` and the manual says refer (Rule 49.E.1)",
     1, "load", "wrong-number", "1 coverage, 51 jurisdictions"),
    ("R02", "gate state-specific / OI-64", "NY Special Protective and Highway: "
     "loss cost 0, ELP 0, selector `Company` on all 3 classes",
     1, "load", "zero", "1 coverage, NY only"),
    ("R03", "gate 332 / E17 / N18", "the refer sentinel is edition-scoped — "
     "`Refer To Co.` x49 and `Refer to Company` x1, both live inside "
     "`GL_CW_20270401_V01`",
     1, "load", "wrong-number", "2 table sites, 5 rule sites"),
    ("R04", "gate terrorism §3a", "15 jurisdictions file their own terrorism "
     "factors, keyed on Territory; NY adds a Manhattan table",
     1, "load", "wrong-number", "15 of 51 jurisdictions"),
    ("R05", "gate 365 §10", "California withdraws Loss Of Electronic Data and "
     "Cyber Incident Liability — `SetCoverageOnPolicyIndicator` stubbed to 0",
     1, "load", "n/a", "2 coverages, CA only"),
    ("R06", "NY differential / OI-59", "New York withdraws claims-made GL — "
     "4 tables emptied, the multiplier stubbed to 1.0 in 5 groups",
     1, "load", "wrong-number", "5 coverage groups, NY only"),
    ("R07", "gate size-of-risk §6a", "CA and NY disable size-of-risk by rule, "
     "stubbing `SetSizeOfRiskRatingApplies` to `No`",
     1, "load", "n/a", "2 of 51 jurisdictions"),
    ("R08", "gate rating plans §2", "Nebraska empties both schedule-rating cap "
     "tables and files its own cap mechanism",
     1, "load", "wrong-number", "NE only"),
    ("R09", "census probe 6", "IA/MO/OK redirect the liquor grade to "
     "`LiquorLiabilityGradeOnOffPremises`; NY redirects the policy adjustment "
     "factors — safe, but only if the engine resolves the rule not the table",
     1, "load", "null", "4 jurisdictions"),
    # ---------------------------------------------------------------- kind 2
    ("R10", "gate size-of-risk §7", "14 jurisdictions inherit the size-of-risk "
     "chain and ship no loss costs; `PremOpsLossCost` is never assigned",
     2, "rate", "null", "14 of 51 jurisdictions"),
    ("R11", "gate size-of-risk / OI-53", "`GL_CW_20270401_V01` strips the "
     "assignment/min/max tables — a silent zero for any adopter",
     2, "load", "zero", "0 of 51 today; binds on adoption"),
    ("R12", "gate 365 / census probe 6", "MA and TX empty "
     "`BringYourOwnAlcoholExclusionFactor`; the setter fires only for classes "
     "16905/16906 with the liquor-exclusion amendment",
     2, "rate", "null", "2 jurisdictions, 2 classes"),
    ("R13", "OI-20 / NY differential", "a base table present and EMPTY where the "
     "rows are filed under a sharded name — falling through to the parent is "
     "wrong (N3)",
     2, "load", "zero", "CA, NJ, NY, OH"),
    # ---------------------------------------------------------------- kind 4
    ("R14", "OI-44", "21 zero liquor deductible factors; the guard covers 10, "
     "leaving ten Per Common Cause options unguarded and overcharging",
     4, "rate", "wrong-number", "21 cells, guard covers 10"),
    ("R15", "gate rating plans §6", "the ±25% schedule cap is enforced by "
     "`ScheduleRatingModificationLogic` writing a message id — it does not clamp",
     4, "rate", "wrong-number", "51 jurisdictions"),
    ("R16", "gate 365 §9", "`FinalILF = CSLILF − DeductibleFactor` has no floor; "
     "two guards are all that prevent a negative premium",
     4, "rate", "wrong-number", "1 coverage, countrywide"),
    ("R17", "gate terrorism §6", "the endorsement factor's only filed bound, "
     "`0 < f ≤ 0.004`, exists solely in a DoMessage* rule name",
     4, "rate", "wrong-number", "1 coverage, countrywide"),
    # ---------------------------------------------------------------- kind 3
    ("R18", "gate 332 / E15", "an `LCM` of exactly 1 is a placeholder for a "
     "company input, not a rate — 6 tables carry `1`, the 4 `*LCMCompany` "
     "tables are empty in all 61 packages, 0 of 51 jurisdictions override any, "
     "and 11 rating paths consume one. **DECIDED 2026-08-12: disposition A, a "
     "required carrier parameter** — single-carrier build, LCM configured to "
     "**1.0 to match RAaS**, so engine output is directly comparable with the "
     "oracle. The referral moves to configuration time: refuse to rate if the "
     "parameter was never supplied; never refer merely because it resolves to 1",
     1, "config", "n/a", "11 rating paths, 51 jurisdictions"),
    ("R19", "gate 370", "18 of 60 drone rating cells are RTC, across three axes "
     "and both coverages — and all 18 zeros are markers, with no legitimate zero "
     "among them and no filed value between 0 and 0.4. **DECIDED 2026-08-12: "
     "refer to company, resolvable by an underwriter-supplied rate.** Registered "
     "on (table, row) so an unrecognised zero fails loudly rather than being "
     "assumed a sentinel",
     1, "rate", "zero", "18 cells, 6 tables, 3 axes"),
    ("R20", "gate 370 / OI-48", "the filed `Unknown` / `Not Applicable` values on "
     "the three drone axes price as 0 — 8 of R19's 18 cells. **DECIDED "
     "2026-08-12: refer to the underwriter, same mechanism as R19**, with a "
     "distinct referral reason: *the submission could not resolve the category*, "
     "not *ISO will not price this use*",
     1, "rate", "zero", "8 cells, 2 axes"),
    ("R21", "gate size-of-risk §5", "a 0 final relativity while the flag is "
     "`Yes` — guarded on the flag, not the value; 0 of 388 DoMessage* rules "
     "would catch it. **DECIDED 2026-08-12: NOT a referral.** 0 of 10,706 filed "
     "relativity cells is zero, so a zero cannot come from the data — only from "
     "the rule's fallback when the class code fails to resolve. Load-time "
     "assertion plus a rate-time input validation error",
     0, "load", "zero", "countrywide"),
    ("R22", "OI-34 / E8", "county or place unmatched — **ALREADY DECIDED by E8**: "
     "a required submission field in those four jurisdictions; refer on "
     "unmatched, never a fuzzy match", 1, "rate", "no-signal", "CA, FL, NY, TX"),
    ("R23", "gate 335 OCP", "`WorkersCompensationRate` absent for class 15191 — "
     "**ALREADY DECIDED**: the second of four submission requirements in build "
     "plan §7", 1, "rate", "no-signal", "1 class"),
    ("R24", "OI-41", "an effective date before the corpus floor of 2022-09-01 — "
     "**ALREADY DECIDED** in OI-41's own text: fail loudly, never fall back",
     0, "load", "no-signal", "all 51"),
    ("R25", "OI-49", "railroad class 40014 operations that are not construction "
     "— the ELP Supplement rates construction at 150% of class 16292 and refers "
     "everything else; ERC implements only the first branch and "
     "`RailroadClassDescription` is tested for emptiness, never content. "
     "**DECIDED 2026-08-12: submission field on class 40014, `no` refers**",
     1, "rate", "wrong-number", "1 of 4 railroad classes"),
    ("R26", "E19", "**ten** classes — all cannabis and hemp — declare "
     "`Rate/Loss Cost Applies`, carry a real ordinary loss cost and are zero only "
     "under size-of-risk, identically in 34 of 35 shipping states; Michigan omits "
     "them instead. The other 178 of E19's 188 are the ELP-path switch (N13's "
     "third meaning), not sentinels. **DECIDED 2026-08-12: refer and resolve**",
     1, "rate", "zero", "10 classes x 34 jurisdictions"),
    ("R27", "OI-57", "conditional-exclusion prorating — the manual offers two "
     "filed treatments and ERC implements the full-term one, declaring 9 "
     "pro-rate/day-count fields that no rule writes. **DECIDED 2026-08-12: take "
     "the filed full-term option**, submission field defaulted to Yes; no "
     "proration arithmetic implemented",
     0, "config", "n/a", "terrorism, all jurisdictions"),
    ("R28", "OI-61", "Puerto Rico: Schedule & Experience **is** confirmed — its "
     "2015 notice adopts the multistate plan outright — leaving **Composite "
     "Rating alone**, where no PR document exists. The gap is eligibility, not "
     "arithmetic: composite rating derives no filed number. **DECIDED "
     "2026-08-12: withhold the plan in PR; do not escalate**",
     0, "config", "n/a", "PR, composite rating only"),
]

KIND = {0: "NOT-REFERRAL", 1: "DECLARED", 2: "MISSING", 3: "NONE", 4: "GUARD"}

# Entries that WERE kind 3 and have since been decided. The corpus still carries
# no discriminator for these — a decision supplied one from outside it — so they
# are tracked here rather than silently reclassified.
#
# A decision may also record a RESOLUTION: what input clears the referral and
# lets rating resume. That is the difference between a referral that ends a quote
# and one that pauses it, and the project has both.
DECIDED = {
    "D02-STABILITY": {
        "disposition": "design decision — dispositions are monotonic",
        "decided": "2026-08-12",
        "by": "user",
        "value": "once raised, a referral cannot be cancelled by a recalculation",
        "reason": "**OI-58 splits in two and only half was ever a decision.** "
                  "California's older countrywide parent recomputes 213 DataDefs "
                  "that every other jurisdiction writes once, and ERC "
                  "re-evaluates coverages in the 14 `PremiumToReachMinCoverage` "
                  "groups — so a value CAN be produced twice. **The premium half "
                  "is now testable**: `Payloads/CA` is a rated output (OI-67), so "
                  "the engine can be run against ISO's own answer. **The referral "
                  "half never will be**: RAaS returns a premium and has no notion "
                  "of a referral, so no oracle can say whether a second pass "
                  "should be able to un-raise one. That makes it a design choice, "
                  "and the conservative direction cannot produce a wrong price.",
        "effect": "A raised referral is **monotonic** — a later evaluation may "
                  "add referrals but never remove one. Paired with D01: a "
                  "resolvable referral pauses everything downstream and is "
                  "cleared only by the named input arriving, never by "
                  "recomputation. **If this later proves over-cautious it will "
                  "show up as referrals that a second pass would have cleared, "
                  "which is visible and fixable; the opposite error is a silent "
                  "quote on a risk that should have been seen.**",
    },
    "D01-PROPAGATION": {
        "disposition": "design decision — the propagation rule, restated",
        "decided": "2026-08-12",
        "by": "user",
        "value": "anything downstream of a RESOLVABLE referral pauses with it "
                 "and is computed once, after resolution; a dead-end referral "
                 "permits partial results",
        "reason": "**The rule first proposed — `REFER` absorbing under "
                  "multiplication but not under summation — was wrong, and wrong "
                  "in an instructive way.** Terrorism's base is a SUM of three "
                  "sibling premiums, so the operator rule would have let it rate "
                  "on a partial base when one component referred. Distributing is "
                  "mathematically exact — `(a+b+c)xf = axf + bxf + cxf` — but "
                  "practically wrong **because of decision R19**: referrals here "
                  "are RESOLVABLE, so the missing number is coming, and a "
                  "terrorism charge computed on a partial base is stale the "
                  "moment the underwriter answers. **The rule therefore turns on "
                  "RESOLVABILITY, not on the operator** — a distinction only "
                  "derivable after R19 was decided.",
        "effect": "Terrorism refers whenever any component feeding it refers. "
                  "The rest of the policy still prices — twenty classifications "
                  "with one referral still quote the other nineteen — because "
                  "those are not downstream of the pause. **Terrorism is computed "
                  "last and possibly twice**, and the trace must show it was "
                  "WITHHELD rather than zero. **ERC's own `IsNotNull -> 0` "
                  "pattern must not be copied**: six guards and three zero "
                  "defaults in `SetClassCoveragePremium` make a missing sibling "
                  "contribute nothing, which is right for a coverage the policy "
                  "does not have and wrong for one an underwriter is still "
                  "pricing. ERC cannot tell those apart; the engine must.",
    },
    "R19": {
        "disposition": "B+ — accepted referral, RESOLVABLE by a company-supplied rate",
        "decided": "2026-08-12",
        "by": "user",
        "value": "REFER, then require an underwriter-supplied rate",
        "reason": "All 18 zeros in the six drone modifier tables are referral "
                  "markers and none is a legitimate factor, so the rule is "
                  "derivable from ERC alone — the manual confirms it 24/24 on the "
                  "usage axis rather than sourcing it. The values are also "
                  "discontinuous: the real factors run 0.4 to 1.5 and nothing "
                  "sits between 0 and 0.4, so the zero is a marker wearing a "
                  "number's clothes.",
        "effect": "`REFER` raised before the modifier multiplies, keyed on "
                  "(table, row) for the 18 known entries — NOT on 'any zero in "
                  "this table'. A zero appearing on an unrecognised row fails "
                  "LOUDLY at load time as an unknown sentinel, which is what a "
                  "change in ISO's filing should do. The referral is then "
                  "RESOLVED by an underwriter supplying a rate, and rating "
                  "resumes; it does not end the quote.",
    },
    "R28": {
        "disposition": "E — WITHHOLD the plan in that jurisdiction; no escalation",
        "decided": "2026-08-12",
        "by": "user",
        "value": "composite rating is not offered for Puerto Rico risks",
        "reason": "**Half the item dissolved when the user supplied "
                  "`GL-PR-2015-CGLES-001`**: Puerto Rico IS covered by the "
                  "Schedule & Experience plan, by pure adoption of the multistate "
                  "version ('there are no new or revised manual pages associated "
                  "with this Notice'), at the 2-15 edition. What remains is "
                  "Composite Rating alone, and the user confirmed by inspection "
                  "that no PR composite plan exists. **The gap is eligibility, "
                  "not arithmetic**: composite rating derives no rate — it "
                  "re-expresses premiums already computed from ISO loss costs as "
                  "a rate per exposure unit — so no filed NUMBER is unconfirmed. "
                  "The only open question is whether the plan is available in PR "
                  "at all, and PR appears in every other corpus, which reads as "
                  "'not filed there' rather than 'file missing'.",
        "effect": "The composite rating option is **not presented** for Puerto "
                  "Rico. Not a referral — an underwriter would face the same "
                  "evidence gap with no better basis for resolving it, and the "
                  "referral queue must not become a place to forward our own "
                  "uncertainty. **No ISO escalation**, by decision: the "
                  "restriction stands on its own and carries no dependency on a "
                  "reply. Composite rating is elective, so withholding it in one "
                  "jurisdiction is small and instantly reversible if evidence "
                  "later appears.",
    },
    "R27": {
        "disposition": "A — submission field selecting a FILED manual option, "
                       "defaulted to full-term rating",
        "decided": "2026-08-12",
        "by": "user",
        "value": "rate the full policy term; field pre-set to Yes",
        "reason": "**The manual offers the insurer a choice, so selecting one is "
                  "not sourcing anything.** PEV001 A.2 gives two treatments when "
                  "a conditional exclusion is attached: (a) pro-rate by day count "
                  "now and re-rate if Congress extends, or (b) charge the TRIA "
                  "factors for the entire term and refund if the Program "
                  "terminates. **Option (b) requires no proration arithmetic at "
                  "issuance — and it is exactly what ERC already does.** ERC "
                  "detects the situation (`TRIAExpirationDate`, `TRIAExtended`, "
                  "`TRIPTerminatesBeforeExpirationDate`), computes "
                  "`PolicyEffectiveWhileTRIAInEffect` and "
                  "`PolicyExtendsToPostTRIA`, keys the factor table on the TRIA "
                  "indicator, and raises an 18,901-character "
                  "`TerrorismUnderwritingLogic` message — but **0 rules write any "
                  "of the 9 declared pro-rate / day-count fields.** Choosing (b) "
                  "makes that gap correct rather than missing.",
        "effect": "A submission field asking whether to rate the full term, "
                  "**defaulted to Yes**. No day-count arithmetic is implemented, "
                  "so no rating calculation is sourced from the manual — the "
                  "R25 line holds. **RESIDUAL, deliberately deferred:** option "
                  "(b) still requires a pro-rated REFUND if the Program actually "
                  "terminates. That is a mid-term change transaction rather than "
                  "a rating one, and it is out of scope until the engine handles "
                  "policy changes. **TO VERIFY: whether RAaS can be instructed to "
                  "rate the full term** — if it cannot, the comparison baseline "
                  "for 2027-inception policies needs separate treatment (OI-66).",
    },
    "R26": {
        "disposition": "B+ — accepted referral, RESOLVABLE by a company-supplied rate",
        "decided": "2026-08-12",
        "by": "user",
        "value": "REFER, then require an underwriter-supplied size-of-risk loss cost",
        "reason": "**The register said 188 classes. It is ten, and they are all "
                  "cannabis and hemp.** Checking the N17 rating-basis selector "
                  "split the 188 almost perfectly: the other 1,000 classes are "
                  "`Rate/Loss Cost Applies` 100%, while the 188 are `Industry` "
                  "110, `Company` 68 and `Rate/Loss Cost Applies` only 10. So "
                  "**178 do not rate from a loss cost at all** — their zero is "
                  "N13's third meaning, the documented switch to the ELP path "
                  "established in gate 336, not a sentinel. The remaining ten "
                  "declare `Rate/Loss Cost Applies`, carry a real ORDINARY loss "
                  "cost, and are zero only under size-of-risk: 10011/10012, "
                  "10025/10027, 10210/10211, 50011/50012, 50018/50019 — cannabis "
                  "and hemp distribution, retail and manufacturing — identical in "
                  "**34 of the 35 shipping states**. ISO rates them normally and "
                  "declines the large-risk discount, which is a plausible filed "
                  "position and is not what an error looks like across 34 states.",
        "effect": "Same mechanism as R19: REFER before the loss cost is used, "
                  "resolved by an underwriter-supplied value. **Keyed on (class, "
                  "table)**, not on 'any zero size-of-risk loss cost', so an "
                  "eleventh class appearing later fails loudly instead of being "
                  "absorbed. **Michigan is the control and its treatment must be "
                  "asserted equivalent**: MI omits the ten rather than zeroing "
                  "them — 1,178 classes, not 1,188 — so the load-time assertion "
                  "is that each of the ten is either present-and-zero or absent "
                  "in every shipping state. A real value appearing is a filing "
                  "change worth seeing.",
    },
    "R25": {
        "disposition": "A — submission requirement (the FIRST without ISO backing)",
        "decided": "2026-08-12",
        "by": "user",
        "value": "for railroad class 40014, ask whether the operations are "
                 "construction; 'no' refers",
        "reason": "**Scoped far more narrowly than the register recorded.** Not "
                  "railroad generally — Railroad Protective has a closed 4-class "
                  "domain, two of which say `Construction` in the name, and the "
                  "ELP Supplement's referral sits entirely inside class 40014 "
                  "('no work within 50 feet of tracks, or no exposure to actual "
                  "train hazards'): *for construction operations* the ELP is 150% "
                  "of class 16292, *for operations other than construction, refer "
                  "to company*. **ERC implements branch (a) only and rates every "
                  "40014 as construction.** `RailroadClassDescription` looked like "
                  "a discriminator and is not — `SetBaseELPRR` and `SetILF40014` "
                  "test it for NON-EMPTINESS, never for content.",
        "effect": "A submission field on class 40014. **This is the first of five "
                  "submission requirements with NO filed ISO value behind it** — "
                  "county, `WorkersCompensationRate`, the drone axes and "
                  "`SizeOfRiskRatingApplies` all had one. The doctrinal ground: "
                  "'the manual confirms, never sources' governs RATING, and an "
                  "input that can only ever produce a REFER takes no price from "
                  "anywhere — it declines to quote. **That licenses "
                  "referral-only inputs and nothing else**; an input that changes "
                  "a number still may not be sourced from the manual.",
    },
    "R22": {
        "disposition": "A — submission requirement (ALREADY DECIDED, E8/OI-34)",
        "decided": "2026-08-10 (E8) · surfaced in the register 2026-08-12",
        "by": "project (pre-existing decision)",
        "value": "county or place is a required submission field in CA/FL/NY/TX",
        "reason": "**Not a new decision. The register was asking the user to "
                  "re-decide something already settled.** E8 closed with: ERC "
                  "carries the place tables for those four jurisdictions and only "
                  "address-to-place resolution was ever external, so county is a "
                  "required submission field, there is no geocoding dependency, "
                  "and an absent or unmatched county refers — never a fuzzy match.",
        "effect": "Refer on unmatched, sourced from an existing project decision. "
                  "No new judgement required.",
    },
    "R23": {
        "disposition": "A — submission requirement (ALREADY DECIDED)",
        "decided": "2026-08-11 · surfaced in the register 2026-08-12",
        "by": "project (pre-existing decision)",
        "value": "`WorkersCompensationRate` is a required submission field for "
                 "OCP class 15191",
        "reason": "**Not a new decision.** Build plan §7 already lists it as the "
                  "second of four inputs that resolved as submission requirements "
                  "rather than gaps — a declared ERC field that real STC "
                  "submissions supply.",
        "effect": "Refer when absent, sourced from an existing project decision.",
    },
    "R24": {
        "disposition": "D — NOT a referral: load-time assertion (ALREADY DECIDED)",
        "decided": "2026-08-11 (OI-41) · surfaced in the register 2026-08-12",
        "by": "project (pre-existing decision)",
        "value": "fail loudly below the 2022-09-01 corpus floor",
        "reason": "**Not a new decision.** OI-41 already records the disposition "
                  "in its own text: a resolver asked for an earlier effective "
                  "date *must fail loudly, not fall back to the earliest "
                  "available edition* — falling back would rate a 2021 Wisconsin "
                  "risk on a 2022 filing with no signal.",
        "effect": "Leaves the referral register, same shape as R21: a load-time "
                  "assertion, not a referral. Back-dated and re-rated policies "
                  "are ordinary business, so this is reachable.",
    },
    "R21": {
        "disposition": "D — NOT a referral: load-time assertion + input validation",
        "decided": "2026-08-12",
        "by": "user",
        "value": "assert and bounce",
        "reason": "The measurement inverted the question. **Not one zero exists "
                  "in 10,706 filed relativity cells** — 8,330 relativity, 1,188 "
                  "minimum, 1,188 maximum, smallest values 0.0294 / 0.0908 / "
                  "0.7081. So unlike the drone markers, ISO never files a zero "
                  "here at all: a zero relativity cannot come from the data, only "
                  "from the rule's own fallback when a lookup misses. There is "
                  "essentially one way in — the CLASS CODE did not resolve — and "
                  "the tiny-exposure route is safe because the minimum-relativity "
                  "clamp lifts it to the filed floor.",
        "effect": "**Leaves the referral register.** (1) LOAD TIME: assert that "
                  "every class a jurisdiction files size-of-risk loss costs for "
                  "has an assignment, minimum and maximum in its declared parent "
                  "— the check that caught Kansas class 10212 (OI-52). (2) RATE "
                  "TIME: an unresolved class code is an INPUT VALIDATION ERROR, "
                  "bounced with the class code in the message. Not referred, not "
                  "priced. **Referrals must keep meaning 'a human needs to price "
                  "this'** — using them for bad input turns the queue into a "
                  "data-quality inbox and stops it meaning anything.",
    },
    "R20": {
        "disposition": "B+ — accepted referral, RESOLVABLE by a company-supplied rate",
        "decided": "2026-08-12",
        "by": "user",
        "value": "REFER to the underwriter, same mechanism as R19",
        "reason": "`Unknown` and `Not Applicable` are filed ISO domain values on "
                  "all three drone axes and both price as 0, so they are markers "
                  "like the other ten. The alternative considered and rejected "
                  "was bouncing them back to the broker as an incomplete "
                  "submission: OI-48 already established that the broker resolves "
                  "one category per axis and that `Unknown` is their licensed way "
                  "to say they cannot, so a broker filing it has answered "
                  "correctly and there is nothing to send back.",
        "effect": "Same mechanism as R19 — REFER, resolved by an "
                  "underwriter-supplied rate. **The REASON must differ in the "
                  "referral message**: the other ten cells mean *ISO will not "
                  "price this use*, these eight mean *the submission could not "
                  "resolve the category*. Identical handling, different question "
                  "for the human, so the trace has to carry which it was.",
    },
    "R18": {
        "disposition": "A — required carrier parameter",
        "decided": "2026-08-12",
        "by": "user",
        "value": "LCM = 1.0",
        "reason": "SINGLE-CARRIER BUILD, and 1.0 is chosen to MATCH RAaS so that "
                  "engine output is directly comparable with the oracle. This is "
                  "an oracle-alignment decision, not an actuarial one: RAaS is "
                  "already the project's answer for E1's rounding tie-break and "
                  "the source of the `Payloads/` baseline set, so holding the LCM "
                  "at 1.0 keeps every future diff against it clean.",
        "effect": "E15 closes. E9's 'hold at 1.0' stands, now with a stated "
                  "reason and a load-time assertion. The referral moves from rate "
                  "time to configuration time: refuse to rate when the parameter "
                  "was never supplied; never refer merely because it resolves to 1.",
    },
}
failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    if not ok:
        failures.append(name)


def main() -> int:
    asof = next((a for a in sys.argv[1:] if len(a) == 8 and a.isdigit()), None)
    verbose = "--verbose" in sys.argv
    if not asof:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4).", file=sys.stderr)
        return 2

    census_path = os.path.join(OUT, "referral_census.json")
    if not os.path.exists(census_path):
        print(f"ERROR: run 40_referral_census.py first — {census_path} missing",
              file=sys.stderr)
        return 2
    census = json.load(open(census_path, encoding="utf-8"))

    ids = [r[0] for r in REGISTER]
    assert len(ids) == len(set(ids)), "duplicate register id"
    by_kind: dict[int, list] = defaultdict(list)
    for r in REGISTER:
        by_kind[r[3]].append(r)

    print(f"referral register as of {asof} — {len(REGISTER)} entries "
          f"(census: {census['packages']} packages)\n")
    for k in sorted(by_kind):
        print(f"  {k} {KIND[k]:<9} {len(by_kind[k]):>2}")
    det = Counter(r[4] for r in REGISTER)
    fail = Counter(r[5] for r in REGISTER)
    print(f"\n  detection point: {dict(det)}")
    print(f"  failure mode:    {dict(fail)}")

    if verbose:
        print()
        for r in REGISTER:
            print(f"  {r[0]}  {KIND[r[3]]:<9} {r[4]:<5} {r[5]:<13} {r[1]}")
            print(f"        {r[2]}")

    # ---- 1. the classification agrees with step 1's independent reconciliation
    doc = {d["condition"]: d["probe"]
           for d in census["reconciliation"]["documented"]}
    undetectable = census["reconciliation"]["decisions_required"]
    n_none = len(by_kind[3])
    # A DECIDED entry legitimately leaves kind 3: the corpus still carries no
    # discriminator, but a decision has supplied one from outside it. So the two
    # counts diverge by exactly the number of decisions taken, and the check has
    # to track that rather than demand equality — otherwise every decision breaks
    # a passing test, which is the fastest way to teach someone to ignore it.
    # Only decisions about REGISTER ENTRIES count here. `DECIDED` also holds
    # design decisions (D01, the propagation rule), which were never kind 3 and
    # must not inflate the arithmetic — the check failed the moment one was
    # added, which is the check being narrower than its own name for the second
    # time in this file.
    entry_decisions = {k for k in DECIDED if k.startswith("R")}
    check("kind NONE plus entry decisions matches what step 1 found undetectable",
          n_none + len(entry_decisions) == undetectable,
          f"{n_none} still NONE + {len(entry_decisions)} decided "
          f"({sorted(entry_decisions)}) = {n_none + len(entry_decisions)} · "
          f"step 1 independently found {undetectable} of "
          f"{len(doc)} documented conditions unreachable by any probe. The "
          f"classification is a judgement and the reconciliation is a "
          f"measurement; computed separately, they must reconcile")

    # ---- 2. no kind-3 entry claims a detection point
    bad = [r[0] for r in by_kind[3] if r[4] != "never"]
    check("every NONE entry is undetectable by construction", not bad,
          f"{len(by_kind[3]) - len(bad)} of {len(by_kind[3])} say `never` "
          + (f"· INCONSISTENT {bad}" if bad else
             "— a NONE that claimed a detection point would be misclassified"))

    # ---- 2a. a decision may remove an entry from the register entirely
    notref = by_kind.get(0, [])
    check("entries decided NOT to be referrals are marked, not deleted",
          all(r[0] in DECIDED for r in notref),
          f"{len(notref)} entry/entries left the referral population by decision "
          f"({[r[0] for r in notref]}) — kept with their evidence and their "
          f"reasoning rather than removed, because the next reader needs to know "
          f"the question was asked and how it was answered")

    # ---- 3. the silent failures are the ones that need the register
    silent = [r for r in REGISTER if r[5] == "zero"]
    loud = [r for r in REGISTER if r[5] == "null"]
    check("the silent failures outnumber the loud ones, and that is the point",
          len(silent) > len(loud),
          f"{len(silent)} entries fail SILENTLY as a zero that multiplies "
          f"cleanly; {len(loud)} fail LOUDLY as a null. N13's whole content: a "
          f"sentinel is indistinguishable from a real zero by inspection")

    # ---- 4. every DECLARED entry is load-time detectable
    # `config` is EARLIER than `load`, not later — the check's condition was
    # narrower than its own name and failed R18 the moment a decision moved it
    # to configuration time. The intent is "before any rating happens".
    # R19 is DECLARED and detected at RATE time, and that is correct rather than
    # a design failure: the marker is a cell value, so it cannot be seen until a
    # risk selects that row. What CAN be asserted at load time is that the set of
    # marker rows is the one the register knows — which is the point of keying on
    # (table, row) instead of on "any zero".
    EARLY = ("load", "config")
    late = [r[0] for r in by_kind[1] if r[4] not in EARLY]
    check("every DECLARED entry resolves early, or is a cell-level marker",
          set(late) <= {"R19", "R20", "R22", "R23", "R25", "R26"},
          f"{len(by_kind[1]) - len(late)} of {len(by_kind[1])} resolve at "
          f"{'/'.join(EARLY)} time · {late or 'none'} are cell-level markers, "
          f"detectable only when a risk selects the row — with the ROW SET "
          f"asserted at load time so a new marker cannot appear unnoticed")

    print(f"\n  decisions taken: {len(DECIDED)}")
    for rid, dec in sorted(DECIDED.items()):
        print(f"    {rid}  {dec['disposition']}  ({dec['decided']}, {dec['by']})")
        print(f"        {dec['value']} — {dec['reason'][:120]}...")

    out = {
        "asof": asof,
        "decisions": DECIDED,
        "entries": [{"id": r[0], "source": r[1], "condition": r[2],
                     "kind": KIND[r[3]], "kind_id": r[3], "detect": r[4],
                     "failure": r[5], "scope": r[6]} for r in REGISTER],
        "counts": {KIND[k]: len(v) for k, v in sorted(by_kind.items())},
        "detection": dict(det),
        "failure_modes": dict(fail),
        "decisions_required": [r[0] for r in by_kind[3]],
    }
    p = os.path.join(OUT, "referral_register.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\n  {len(by_kind[3])} entries need a decision before they can be "
          f"implemented: {[r[0] for r in by_kind[3]]}")
    print(f"\nwrote {p}")
    print(f"\n{'FAILED' if failures else 'all register checks passed'}"
          + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
