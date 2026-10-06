# CF Rating Visualization: backlog

Paused 2026-10-06. Pick up from the **Remaining** table. Each page is verified against ISO's rule XML and offline engine
probes, built in `CF_Algorithm/cf-*-chains.html`, then mirrored to the Ideation site under ISO Project Index → Rating
paths → CF Rating Visualization.

## Published (11 pages + index)

| Page | Harness file | Ideation page | PR |
|---|---|---|---|
| Basic Group I | `cf-bgi-chains.html` | `cf-rating-visualization/` (index.html) | #708 |
| Basic Group II | `cf-bgii-chains.html` | `basic-group-ii.html` | #713 |
| Broad | `cf-broad-chains.html` | `broad.html` | #714 |
| Special | `cf-special-chains.html` | `special.html` | #716 |
| Earthquake | `cf-earthquake-chains.html` | `earthquake.html` | #718 |
| All-coverage chains → index only | `cf-rating-chains.html` | `cf-rating-paths/rating-chains.html` | #720 |
| Terrorism / TRIA (chunk 13) | `cf-terrorism-chains.html` | `terrorism.html` | #721 |
| Blanket rating (chunk 9) | `cf-blanket-chains.html` | `blanket.html` | #725 |
| Flood (chunk 25) | `cf-flood-chains.html` | `flood.html` | #726 |
| Builders Risk (chunk 24) | `cf-builders-risk-chains.html` | `builders-risk.html` | #729 |
| Endorsement families (chunk 12) | `cf-endorsement-chains.html` | `endorsements.html` | #731 |
| Leasehold Interest (chunk 11) | `cf-leasehold-chains.html` | `leasehold-interest.html` | #732 |

## Remaining (not started)

Suggested order: 14, then 17, then the rest.

| # | Family (chunk) | Why / what to cover | Chunk records |
|---|---|---|---|
| 1 | **Policy assembly** (14) | Ties every page together: IRPM, package modification, multi-premium credit, the policy total and stat codes. `CF_Account_Premium_Bracket.html` already draws the roll-up; this would be the chain view. | `docs/CF-CHUNK14-*` |
| 2 | **Business Income add-ons** (17) | The largest remaining family (Extended Period of Indemnity, Off-Premises, etc.); the Off-Premises flood factor already appears on the Flood page. | `docs/CF-CHUNK17-*` |
| 3 | **Valuation and condition modifiers** (18) | Modifiers that move the core chains (Functional Valuation, Agreed Value, etc.). | `docs/CF-CHUNK18-*` |
| 4 | **Scheduled property items** (19) | | `docs/CF-CHUNK19-*` |
| 5 | **Small coverages with their own tables** (20) | Possibly a single summary page. | `docs/CF-CHUNK20-*` |
| 6 | **Sewer backup and condo options** (21) | | `docs/CF-CHUNK21-*` |
| 7 | **Value reporting and special coinsurance** (22) | The reporting-form branches already show up on the Building / Contents pages. | `docs/CF-CHUNK22-*` |
| 8 | **State-only coverages** (23) | No countrywide file; state map is the page. | `docs/CF-CHUNK23-*` |

## Method (as used for the 11 pages)

1. Scope the family from its chunk gate (`docs/CF-CHUNKnn-GATE.md`, "What the chunk established") and the rule files
   under `F:\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Rules`.
2. Split into 1–3 verification agents. Each one: reads the XML for CW 2023-08 V04 and CW 2026-06 and diffs them; scans
   state overrides at both dates; probes the engine **offline only** (no `--live`) at a CW 2023-resolving and a CW
   2026-06-resolving date in a clean state plus an override state, reusing the chunk's builders and
   `scripts/cf/_state_inputs.py`; checks which zero endings refuse after 542f0e1; writes a scratch `.md` with mermaid
   diagrams, titleblock facts, notes, a delta note and a "chunk claims re-checked" table.
3. Build the page from `cf-bgi-chains.html`'s head and script (keeps the hash deep-linking), render-check every diagram
   in Chrome, commit only the page.
4. Mirror to Ideation (`projects/iso-rating-engine/cf-rating-visualization/`), add it to `artifact.json` and to the
   project index (sidebar leaf, overview row, card, group count), open the PR and merge it.

## Open questions the pages raised (for the Harness / chunk 28, not rating docs)

* **Blank `RatingTypeBasicGroupII`** prices Group II $0, "rated", in the 36 states that require it: Building, Contents,
  BI, Debris Removal, Leasehold. Not covered by C28-17; chunk 28's test ran only in Oregon, which doesn't read it.
  (`cf-bgii-chains.html`, `cf-leasehold-chains.html`)
* **NY post-TRIA with NY's own values** charges BI $53 / SCBI $55: needs one live ISO call. (`cf-terrorism-chains.html`)
* **Flood BI blank / "Not Applicable" TypeOfRisk** refuses (always-true `Or`) where SCBI's `And` prices $0; ISO not
  asked. (`cf-flood-chains.html`)
* **Builders Risk premium adjustment:** a missing unit-1 period or blank UnitNumber charges the whole annual premium
  (OI-115 null-subtract); not checked at ISO. (`cf-builders-risk-chains.html`)
* **Business Income Group I adjustment factor:** a 2026-09-18 note says it applies first (Oregon); the CW rule applies
  it last. Marked unreconciled in `CauseOfLoss_BusinessIncome_RatingAlgorithms.md`.
* **Operational-unit Earthquake BI rate** is always 0 (`SetHighestBusnIncomeEQBaseRate` never writes its maximum);
  not checked at ISO. (`cf-earthquake-chains.html`)
