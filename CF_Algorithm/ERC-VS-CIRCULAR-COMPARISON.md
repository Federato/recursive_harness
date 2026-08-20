# CF: ERC-side vs. Circular-side — the independence cross-check

**What this is.** GL's engine was only trusted to start once two independently-built analyses —
one reading ISO's filed manuals, one reading ISO's machine-readable data files, each blind to the
other's conclusions — were compared and found to agree. This document is that same check, run for
Commercial Fire, for the first time.

**How it was kept honest.** `Agentic/cf-erc-expert/knowledge/*.json` was built by reading only
`C:\Projects\ISO_ERC_Files\CF\` — the raw data files — with an explicit, enforced rule not to open
`CF_Algorithm/`, `CFBranch/`, or `Agentic/cf-circular-expert/` while doing it. This document is the
first place the two sides are read side by side.

---

## Where they agree

**The countrywide package holds the method, not the money — found twice, independently.**

- *Circular/manual side* (`CF_Algorithm/Coverage_Inventory_And_Tracking.md`): reported
  `SpecialBuildingRate.RateTable.csv`, `BasicGroupIRate.RateTable.csv`,
  `BasicGroupIIRate.RateTable.csv`, `LowestBasicGroupIIRate.RateTable.csv`, and
  `BaseRateAdjustmentFactor` as header-only at the countrywide level — no data row, so Building
  rating can't resolve to a number without a state filing.
- *ERC side* (`Agentic/cf-erc-expert/knowledge/table_catalogue.json`, built with no access to the
  above): independently found **103 of 460 countrywide rate tables (22.4%) are header-only**, and
  base-rate tables specifically are empty **58% of the time**. The ERC side then traced an actual
  premium chain end to end — `SetSpecialBaseRate` → `LookupSpecialBuildingRate` →
  `SetSpecialRate` → `SetSpecialCauseOfLossAdjustment`
  (`CommercialPropertyStructureRules.Rule.xml:9611-9711`) — and found the table that chain reads,
  `SpecialBuildingRate.RateTable.csv`, is exactly one of the header-only tables the manual side had
  separately flagged.

This is the same shape as GL's central early finding, reached the same way GL's was: two processes
that couldn't see each other's work, landing on the same table by name.

## Where the comparison found something neither side had caught alone

**Hawaii isn't just unreviewed on the manual side — it may not exist in ISO's CF filings at all,
and nobody had noticed.**

- *ERC side*: a full census of all 8 edition folders under `C:\Projects\ISO_ERC_Files\CF\` found
  **HI, ID, LA, MS, WA structurally absent** — no package directory for these jurisdictions exists
  anywhere in the corpus, in any edition.
- *Circular/manual side* (`CF_Algorithm/Circular_Review_Tracking.md`): has explicit rows for
  Idaho, Louisiana, Mississippi, and Washington, each marked *"Access needs to be secured"* — a
  known gap, being tracked. **Hawaii has no row in that ledger at all** — not reviewed, not marked
  pending, not mentioned.

Read separately, each side looks complete on its own terms: the manual side has a clean list of
four known gaps to close, and the ERC side has a corpus that (aside from those same four) looks
otherwise full. It's only holding them together that surfaces the fifth gap — the one nobody was
tracking, because nobody had gone looking for what should be there and wasn't. This is the exact
value the two-source method exists to produce, and it is CF's first hit of the same kind that
found GL's missing territories.

## A structural difference worth flagging, not yet cross-checked

The ERC side found **no ZIP-code-keyed territory table anywhere sampled** (countrywide plus 9
states, including CA, NY, TX) — every sampled state uses a county/place-name table instead, or a
single countrywide territory for small states. This is a real difference from GL, where 27
jurisdictions use ZIP-code territories. It has not yet been checked against the manual side's own
description of CF's territory rules — that's a natural next comparison, not done here.

Also unconfirmed on the manual side: the ERC census found **FL, IL, and NJ packages missing from
the current (20260601) edition specifically**, though present in earlier editions — a different
kind of gap from Hawaii's (an edition lapse, not a jurisdiction ISO doesn't file). Whether this
reflects a real filing gap or an ERC snapshot/licensing quirk is not yet known from either side.

## What this does not yet establish

This compares two *analyses*, not two *complete* pictures of CF. The ERC-side knowledge base
indexes the countywide package and one recent edition in full, and samples (not fully surveys)
territory schemes and the rule model — it does not yet cover the state-level packages the way the
final engine will need to. Extending both sides' coverage, and re-running this comparison as they
grow, is future work, not part of what item 1 was scoped to produce.

---

**Produced 2026-08-20**, as the first of what should become a running comparison, following item 1
of `docs/CF-PROPERTY-INTEGRATION-PROPOSAL.md`.
