# CF payload spec — completion tracker

Tracks what remains before the CF rating-payload specification is complete, starting with
class-rated Building and Personal Property in Alabama.

**Opened:** 2026-09-17
**Spec document:** `CF_Algorithm/CF_Payload_ClassRated_Bldg_PP_Alabama.md`
**HTML companion:** `CF_Algorithm/CF_Payload_Completion_Tracker.html`

Status values: **OPEN** · **IN PROGRESS** · **DONE** · **BLOCKED** (needs something outside
the ERC files)

---

## Scoreboard

| Set | Item | Status |
|---|---|---|
| 0 | `ConstructionType` → `ConstructionCode` mapping | **DONE** 2026-09-17 |
| 0 | `Group` A/B/C derivation | **DONE** 2026-09-17 |
| **1** | 1a `ClassCodeToUse` derivation | **DONE** 2026-09-17 |
| **1** | 1b `YARD` selection | **DONE** 2026-09-17 |
| **1** | 1c Validate payload against all 7 AL STC cases | **DONE** 2026-09-17 |
| **1** | 1d Basic Group II specification | **DONE** 2026-09-17 |
| 2 | 2a Index the STC corpus | **DONE** 2026-09-17 — `STC_Corpus_Index.xlsx` |
| 2 | 2b Find AL rating paths with no STC coverage | **DONE** 2026-09-17 |
| 2 | 2c Determine whether expected outputs ship with STC | **DONE** 2026-09-17 — **no** |
| 3 | 3a Personal Property CovType universes beyond `All Personal Property` | **DONE** 2026-09-17 |
| 3 | 3b Broad and Special forms | **DONE** 2026-09-17 |
| 3 | 3c Second state — the District states (AK, CA, NY) | **DONE** 2026-09-17 |
| 4 | 4a Live RAaS envelope (`header`/`body` wrapper) | **DONE** 2026-09-17 |
| 4 | 4b `LossCostMultiplier` sourcing | **DECIDED** 2026-09-17 — default `1.0` |
| **6** | 6a Carrier LCM as configured input, by LOB | **OPEN** |
| **6** | 6b Carrier deviation layer beyond LCM | **OPEN** |
| **7** | 7a Inventory the `DoMessage` validation rules | **DONE** 2026-09-17 |
| **7** | 7b Map mirrored rule pairs | **OPEN** |
| **7** | 7d Message register + diagnostic loop | **DONE** 2026-09-17 |
| **7** | 7e Pre-flight payload validator | **NOT STARTED** — needs explicit go |
| **7** | 7c Reachability: which messages can fire for a given payload | **OPEN** |
| 5 | Rating engine | **NOT STARTED** — parallel work in flight; needs explicit go |

---

## Set 0 — closed before the tracker opened

### `ConstructionType` → `ConstructionCode` — DONE
`SetConstructionCode` (`CommercialPropertyStructureRules.Rule.xml` line 1041) calls
`LookupConstructionCode`, which reads the **`ConstructionCode` rate table**, keyed
`StateCode + ConstructionTypeToUse`, state first with `CW` fallback. Six countrywide rows,
no state override anywhere: Frame 1, Joisted Masonry 2, Non-Combustible 3, Masonry
Non-Combustible 4, Modified Fire Resistive 5, Fire Resistive 6.

### `Group` A/B/C derivation — DONE
`SetGroup` (`CommercialPropertyOccupClassRules.Rule.xml` line 640) reads only `RatingType`,
`ClassCodeToUse` and `ClassCode`, and assigns `A` / `B` / `C` / `Not Applicable`.
`RatingType ≠ Class` short-circuits to `Not Applicable`; the building's `ClassCodeToUse`
gates against ten eligible codes; the occupancy class's own `ClassCode` selects the letter.

---

## Set 1 — finish the Alabama specification

*What it buys: a payload spec with no known holes, for one state and one form, ready to
hand to whoever builds a submission UI or test harness.*

### 1a — `ClassCodeToUse` derivation — DONE 2026-09-17
Six class-code datadefs across three levels, all derived from the two `ClassCode` values
the payload supplies. Structure's `ClassCodeToUse` is a **plain copy** of `ClassCode`.
OccupClass's is `RatingType = "Class" ? BldgClassCode : ClassCode`. PP copies down.

**Correction made:** `VacantBuilding = "Yes"` does **not** substitute class code `1180`
into the rating path — it sets `ClassCodeForStat`, a statistical code. `ClassCodeToUse` has
no vacancy branch. Vacancy enters BGI through the additive `VacantBuildingRate` instead.
Spec §6.1.

### 1b — `YARD` selection — DONE 2026-09-17
There are **two** `SetGroup` rules. OccupClass's (line 640) assigns `A`/`B`/`C`/
`Not Applicable` and never YARD. PersonalProperty's (line 1640) assigns `YARD` when
`BldgClassCode` ∈ {1400, 1650, 1700} **and** `YardPropertyIndicator` is Combustible or
Non-Combustible. `YardPropertyIndicator` is therefore a required payload input for yard
risks, and is the only route to YARD rating. Spec §6.2.

### 1c — Validate against all 7 AL STC cases — DONE 2026-09-17
Aggregated 7 policies / 7 locations / 7 structures / 4 occupancy classes / 4 PP records.
Policy (14 fields) and OccupClass (8) are **fully stable** — every field in every case.
Structure has 38 of 49 universal, PP 14 of 16.

**Found:** `ConstructionCode` appears directly in 1 of 7 cases — it **can be supplied as an
override**, because `SetConstructionCode` assigns only when null. Spec §3.6.

### 1d — Basic Group II — DONE 2026-09-17
Specified. BGII rates off **rating territory + construction symbol**, not class code +
construction code; territory is a base-rate *key*, not a multiplier. Extra payload drivers
documented (`BasicGroupIIRatingTerr`, `NumStories`, `RatingTypeBasicGroupII`, `OpenSides`,
`BCEG`/`BCEGClass`, `WindstormOrHailDeductible`, the roof/IBHS set, and the
windstorm-or-hail exclusion election). AL base-rate grid transcribed: Seacoast ≈ 3.5×
Inland, Beach ≈ 6×. Spec §7.

**Defect found — see Findings below.**

---

### Findings raised by Set 1

**ISO filed-data defect — `LowestBasicGroupIIRate`, AL, symbol `A`, `PersProp`.**
`CF AL 20270301 V01` files **0.8**. All seven prior AL editions file **0.08**, and every
other symbol in the table still matches its Inland Territory rate exactly. Swept all 48
states' latest packages: only Maine shows anything comparable (0.03 vs 0.028, 0.033 vs
0.032 — small enough to be a deliberate floor). Alabama's is a 10× jump that also breaks
its own edition history.

*Impact:* a class-rated personal property risk with a windstorm/hail exclusion at
construction symbol A, in Alabama, at the current edition, rates BGII contents ~10× too
high — the exclusion branch rebuilds from `LowestBasicGroupIIBaseRate`.

*Action:* raise with ISO. **Do not code around it.** Belongs in
`Rater_Simplifications_Backlog.md` as a divergence if it is ever worked around.

---

## Set 2 — make the STC corpus usable

*What it buys: knowing what ISO itself treats as a valid request, across every state — and
whether we have test data or test data **with answers**.*

### 2a — Index the corpus — DONE 2026-09-17
**`STC_Corpus_Index.xlsx`** (repo root). One row per payload: line, jurisdiction, package
edition/version, case id, `ProductName`, payload effective date, record counts per datadef
level, coverage-slot count, and the switch values each case exercises (`PolicyType`,
`RatingType`, `CovType`, `CauseOfLoss`, `IncludedInBlkt`, `CovForm`, `Subline`,
`VacantBuilding`, `RatingTypeBasicGroupII`, `Group`, `BlktRated`).

**The count is 921, not 924.** Three files in `STC/` folders are **not ISO's** — they are
named `1. Input.json` / `1. Output.json`, matching this project's own `Payloads/<ST>/`
convention, and sit in `GL NJ 20250301 V01` and `GL OK 20250601 V01`. The OK output file
differs from the repo copy at `Payloads/OK/`. They appear to have been dropped into the ERC
tree by us and should be moved out — they pollute any scan of ISO content.

| | CF | GL |
|---|---|---|
| Payloads | 364 | 557 |
| Jurisdictions | 47 | 51 |
| Per jurisdiction | 4 (FL, KS, PR) – 13 (DE) | 5 – 21 |

CF: 206 cases carry Personal Property, 82 Business Income, 28 Special Class.

### 2b — Uncovered AL rating paths — DONE 2026-09-17
Alabama's 7 cases collapse to **two scenarios**, each repeated once per edition:
BPP class-rated Special (4), and vacant Builders Risk Special (3).

Every AL case is `PolicyType = Commercial Property Policy`, `RatingType = Class`,
`IncludedInBlkt = No`, **`CauseOfLoss = Special`**. Not one Basic. Not one Broad. No SPP, no
Specific/Tentative, no blanket, no Legal Liability, no Condominium Association, no Leasehold
Interest.

**This is not an Alabama quirk — it is the whole CF corpus.** Across all 364 CF payloads:

| Switch | Distribution |
|---|---|
| `PolicyType` | **364 / 364 Commercial Property Policy** — zero SPP |
| `RatingType` | **364 / 364 Class** — zero Specific, zero Tentative |
| `IncludedInBlkt` | **364 / 364 No** — zero blanket |
| `CauseOfLoss` | Special 357 · Broad 19 · **Basic 3** · Special Incl/Excl Theft 5 |

**All three Basic cases are Builders Risk** — IL 2025-07-01, IN 2025-10-01, NY 2023-05-01 —
and Builders Risk (class code `1150`) takes a different base-rate branch. So **no CF payload
anywhere exercises a normal class-rated Basic Group I building.** Broad appears in 19 cases
across 11 states; Alabama is not among them.

Contrast GL, which is broader by subline: 519 of 557 are Premises/Operations and
Products/Completed Operations, but Owners and Contractors, Railroad, Liquor and Product
Withdrawal all appear.

### 2c — Do expected outputs ship? — DONE 2026-09-17 — **NO**
**The STC corpus is inputs only.** Every one of the 913 STC folders contains `.json` and
nothing else. Scanning all 921 genuine `STC_*.json` files for premium- or rate-shaped output
keys returns **nothing** — the only match is `WorkersCompensationRate` in 7 files, which is a
Stop Gap *input*.

The premium values that first appeared in the scan (`ErcCalculatedTotalPremium = 7839.0`,
`Premium = 7839.0`) came exclusively from the three locally-added files described in 2a —
our own GL output, not ISO's.

**Consequence, and it is a real constraint:** these are **fixtures, not a regression suite**.
They tell you what a valid request looks like and which paths ISO itself exercises. They
cannot tell you whether a premium is right. Verifying premium still requires calling ISO's
rating service — the STC corpus gives you the inputs to send, not the answers to check.

### Findings raised by Set 2

**1. The corpus cannot verify a premium.** Inputs only — see 2c. Any plan that assumed
"ISO ships test cases, so we can regression-test against them" needs revising. They are
request fixtures; the oracle is still ISO's rating service.

**2. The Basic Group I chain has no representative test case anywhere in CF.** The spec
this tracker serves is centred on Basic Group I, and 361 of 364 CF payloads are Special or
Broad. The 3 Basic cases are all Builders Risk, which rates off a different branch. Building
a BGI implementation means building it with **no ISO-authored example of the path**.

**3. Whole switches are untested corpus-wide.** Standard Property Policy, Specific and
Tentative rating, and blanket (`IncludedInBlkt = Yes`) each appear in **zero** of 364 CF
payloads — yet `CF_RatingPath_Switches.md` identifies `PolicyType`, `RatingType` and
`IncludedInBlkt` as three of the five widest-reaching switches in the line. The most
consequential branches are the least exemplified.

**4. Three of our own files are sitting in ISO's corpus.** `1. Input.json` in GL NJ, and
`1. Input.json` / `1. Output.json` in GL OK. They should be moved out of
`ISO_ERC_Files\` — any future scan of "what ISO ships" will pick them up, and one of them
already contaminated the first output scan in 2c.

---

## Set 3 — extend across coverages and states

*What it buys: knowing whether "starting with Alabama" scales to 47 states or whether each
state is its own project.*

### 3a — PP `CovType` universes — DONE 2026-09-17
`DomainCovTypePrsnlProp` offers **16 values**, keyed `StateCode + PolicyType + CovForm` —
the legal list changes with both. **Only three change rating:**
`Valuable Papers and Records - Other Than Electronic Data` (7 tests, in the BGI/BGII
cause-of-loss adjustments and `SetBroadRate`), `Personal Property in a Vault with an
Approved Fire Rating` (gates `SetFireSafeVaultFactor`), and `Tobacco Sales Warehouses`.
Every other value reaches only `DoMessage*` validation and `AttachForm*` rules.

**Found — a dead test.** The three LOI-factor rules guard on
`CovType <> "Tobacco Sales Warehouses"`, but that string is offered by **zero rows** in all
23 packages that file `DomainCovTypePrsnlProp`. The guard can never be false. Tobacco
warehouses rate via the `CovForm` and their own coverage record instead. Legacy constant,
not a value to support. Spec §3.7.

The STC corpus uses `All Personal Property` and nothing else, in all 364 CF cases — 15 of
the 16 values have no ISO-authored example anywhere.

### 3b — Broad and Special forms — DONE 2026-09-17
**Broad** is the shortest chain (6 steps, **no cause-of-loss adjustment rule at all**).
`BroadFormBaseRate` keys `StateCode + ConstructionTypeToUse + CovType`; **Alabama does not
file it** — countrywide, two-tiered on construction (Bldg 0.015 / 0.010, PersProp
0.021 / 0.011, BldrRisk flat 0.012). No new payload fields required.

**Special Building is a flat statewide constant** — `SpecialBuildingRate`, one row per
state, AL = **0.039**. No class, construction, territory or protection class.

**Special Contents is the odd one out in the whole line.** `SpecialPrsnlPropRate` keys
`StateCode + OccupCategory + OccupCategorySeverity` — an occupancy axis no other form uses.
AL files 13 rows across 8 categories; `SpecialPrsnlPropTheftExclusionFactor` keys on
`OccupCategory` alone. Spec §8.

**Two payload fields Basic never needed:** `OccupCategory` and
`OccupCategoryRiskSeverity`, both declared on OccupClass *and* PersonalProperty.

**Naming trap:** the datadef is `OccupCategoryRiskSeverity`; the rate-table column is
`OccupCategorySeverity`. Different strings, bound positionally. Grepping the rules for the
column name returns nothing — the wrong conclusion.

**Defect found — see Findings below.**

### Findings raised by Set 3

**`OccupCategoryRiskSeverity` — required, undocumented, and absent from every fixture.**
The Special Contents rate key needs it. It appears in **zero of the 364 CF STC payloads**.
**No domain table constrains it** anywhere in the corpus, so its legal values
(`High` / `Medium` / `Low` / `Not Applicable`) are discoverable only by reading the rate
table itself.

Six STC cases use `OccupCategory = "Mercantile"`, and all six are in states filing three
distinct Mercantile severity rows:

| State | High | Medium | Low | Spread |
|---|---|---|---|---|
| CO | 0.267 | 0.239 | 0.135 | 1.98x |
| ME | 0.156 | 0.152 | 0.094 | 1.66x |
| MI | 0.389 | 0.366 | 0.204 | **1.91x** |
| NM | 0.221 | 0.178 | 0.141 | 1.57x |

Either the engine applies a default severity that is written down nowhere, or ISO's own
fixtures are underspecified for Special Contents on any multi-severity occupancy
(Mercantile, Institutional, Industrial and Processing, Service). A submission builder must
supply the field and can learn its values from neither a domain list nor an example.

*Action:* resolve before trusting any Special Contents premium on those four categories.
This is the sharpest open question in the spec — and it sits on the form that 357 of 364
fixtures use.

**Widened by 3c:** this is not a four-state problem. The severity structure is identical in
**all 45 jurisdictions** that file `SpecialPrsnlPropRate`, on the same four occupancy
categories. So the field is required nearly line-wide, has no domain list anywhere, and has
no example in any of the 364 fixtures.

**Also raised by 3c — two dead artefacts that read as required inputs.** Alaska's
`DomainDistrict` is header-only in all 9 of its editions, and
`BasicGroupIDistrictTerritory` is a countrywide Location field no rule reads. Both are
traps for anyone building a submission form from the DataDef. Worth a standing check:
*a declared field with no rule consumer, and a domain table with no rows, should be flagged
rather than surfaced as an input.*

---

### 3c — Second state: the District states — DONE 2026-09-17
Tested against **AK, CA and NY** — the three that split the Basic Group I base rate. (AK was
flagged by the user; the earlier note treating this as a CA/NY question was incomplete.)

**They are not one mechanism. They are three:**

| Mechanism | States | Tables |
|---|---|---|
| Single table | **43** | `BasicGroupIRate` |
| District I / II | **2** — AK, CA | `BasicGroupIDistrictIRate` + `…IIRate` |
| NYC split | **1** — NY | `BasicGroupIRate` + `BasicGroupIRateNYC` |
| None filed | 2 — CW, PR | — |

All variants keep the **same five keys** and the same shape — only *which table* is read
changes. Each state overrides `SetBasicGroupIBaseRate` with its own selector:

- **CA** reads **`../../District`** — a Location field, `District I` / `District II`.
- **AK** reads `BasicGroupIRatingTerr` ∈ {020, 040, 050, 100}.
- **NY** reads `BasicGroupIRatingTerr` ∈ {030, 240, 310, 410, 430} → the NYC table.

**Payload answer: the record shape holds; exactly one state adds one field.** California
needs `District` on `CommercialPropertyLocation` (`DomainDistrict`, 2 rows, CA only).
Alaska and New York need **nothing new** — both derive the split from a territory field
every payload already carries. Spec §9.

**Two dead artefacts found.** `DomainDistrict` is **header-only, 0 rows, in all 9 Alaska
editions** — a dropdown offering nothing, for a field AK's rules never read.
`BasicGroupIDistrictTerritory` is declared on Location countrywide and read by **no rule**.
Neither should be sent; both look required if you read the DataDef instead of the rules.

**The severity axis generalises completely.** `SpecialPrsnlPropRate` is filed by **45 of 47
jurisdictions** (countrywide is empty — Special Contents is entirely state-filed), and the
severity structure is **identical in all 45**: Mercantile High/Medium/Low; Institutional,
Industrial and Processing, Service High/Low; the other four Not Applicable. Only the rates
differ. Florida partitions Special into Residential (flat) and NonResidential (the standard
severity table); Puerto Rico files a different structure again.

---

## Set 4 — needed something outside the ERC files

### 4a — Live RAaS envelope — DONE 2026-09-17
**Confirmed, and no longer blocked.** A live request is
`{ "header": {...}, "body": { "SchemeKeys": {...}, "CommercialProperty": [...] } }`.
The header carries `quoteback` (empty string in every observed request) and
`authorization.orgId` / `authorization.shipId`. Evidence was already in the repo: the real
GL RAaS inputs at `Payloads/<STATE>/1. Input.json` carry the populated authorization block,
while `Engine_Payloads/<STATE>/submission.json` has it empty — which is why earlier reading
suggested the block was unused.

**An STC file is the `body` alone**, with no wrapper. Both statements are true and need to
be kept apart: the header belongs to the account, the body to the risk.

`orgId` and `shipId` hold the same value for this account. They are separate fields and
should not be collapsed into one.

### 4b — `LossCostMultiplier` sourcing — DECIDED 2026-09-17
**Default `1.0`.** LCM appears in no STC payload. At 1.0 the filed ISO loss cost passes
through unchanged, which is the right baseline for proving the engine against ISO — a
carrier multiplier would make every comparison a comparison of our arithmetic rather than
of ISO's. Carrier LCM becomes a configured input (Set 6), never a submission field.

*Consequence to keep visible:* every rate in the spec is an **ISO loss cost, not a carrier
rate**. Nothing produced under this default is a quotable premium.

---

## Set 6 — carrier configuration

*What it buys: the step from "matches ISO" to "matches what this carrier files". Deliberately
after the engine proves itself against ISO, not before — otherwise there is no clean baseline
to prove against.*

### 6a — Carrier LCM as a configured input, by line of business — OPEN
Replace the `1.0` default with a per-carrier, per-LOB configured multiplier. Requirements
known so far:

- **Keyed by LOB at minimum** (CF and GL differ), and realistically by state and effective
  date as well — LCMs are filed and change on their own schedule.
- **Not a submission field.** It must not be settable per-request, or a caller can quietly
  change the rate basis.
- **Not a post-hoc scalar.** `BasicGroupIRate` multiplies the base rate by LCM *before* a
  3-decimal rounding step, so the multiplier changes which side of a rounding boundary a
  rate falls on. Applying LCM to a finished premium gives a different answer than applying
  it in-chain. It has to sit where ISO put it.
- **Provenance.** A result should record which LCM produced it; otherwise stored premiums
  become unreproducible the first time a carrier refiles.

### 6b — Carrier deviation layer beyond LCM — OPEN
LCM is the simplest carrier deviation. Others (rate deviations, own factor tables, own
class plans) will need the same treatment. Scope not yet assessed. GL's
`docs/EXECUTIVE-SUMMARY.md` already describes how carrier deviations layer on top — check
whether that design transfers before inventing a second one.

---

## Set 7 — validation messages

*What it buys: submissions that come back clean. The payload spec says what a request
carries; these rules say whether ISO considers it coherent. A payload can rate **and**
return errors — that is how this set was opened.*

### 7a — Inventory the `DoMessage` rules — DONE 2026-09-17
**`CF_Validation_Messages.xlsx`** (1,621 rows) and **`CF_Validation_Messages.md` / `.html`**.
Every `DoMessage*` rule in the latest package of all 48 jurisdictions, with its message
text, datadef group, check kind, the fields it reads and the records it requires or forbids.

Headline findings:

- **Every message is an "Error".** One helper, `AddErrorMessage`, 621 countrywide calls. No
  warning or informational variant exists. Severity is the caller's problem.
- **434 countrywide rules; 233 more exist only in state packages.**
- **States switch countrywide messages off** by overriding the rule with `<rul:Sequence />`
  — an empty body. **316 such no-ops**, concentrated in FL (63), PR (49), NY (34), KS (20).
  Effective message counts run **400 (PR) to 455 (CA)**, median 437. Alabama suppresses
  none and adds 18.
- **Over half the rules are form-attachment checks** — "you chose X, so endorsement Y is
  mandatory / prohibited" — not data-quality checks.
- **`CovType` drives more messages than any other field** (59 of the 305 spine rules),
  matching its status as the most rating-significant switch.

### 7b — Map mirrored rule pairs — OPEN
CP 03 20 has an opposite: one rule fires if the form is missing when deductibles differ,
another if it is attached when they are the same. Attaching an endorsement to silence one
message can raise its mirror. These pairs were found by hand; there is no systematic list,
and without one "attach everything" looks like a fix and is not.

### 7d — Message register and diagnostic loop — DONE 2026-09-17
**`CF_Message_Register.md` / `.html`** — a running log of every message ISO actually
returns, with root cause, fix, and the *check that was missing*. Seeded with M-001 (CP 03 20).

**`scripts/cf/07_diagnose_message.py`** — given a message text (or rule name), the
`TableName` from the response, the state and optionally the payload, it finds the rule,
decodes the condition, and prints every comparison with the payload's actual value and
whether it is true. Field-to-field comparisons included — those are usually the deciding
half and the easiest to miss by eye. It reports whether the state **suppresses** the
countrywide rule.

It deliberately does **not** evaluate And/Or nesting. A partial evaluator that mishandles a
nested `Or` would be worse than none.

**Standing checks the register has raised so far** (neither built):
C-1 deductible coherence across fields and levels; C-2 assert a mirror rule will not fire
before attaching an endorsement.

### 7e — Pre-flight payload validator — NOT STARTED
Run the applicable `DoMessage` conditions locally before sending, so messages are designed
out rather than discovered. The rule inventory it needs already exists. **Engine-adjacent —
needs an explicit go**, like Set 5.

### 7c — Reachability — OPEN
The 1,621 rules were inventoried by reading conditions, not by evaluating them. Which of a
state's ~440 effective messages can actually fire for a given submission is unanswered.

---

## Set 5 — the engine

`cf_engine/` has package discovery and edition resolution only — no interpreter, no rating
kernel. Everything in the spec is a *reading* until something executes it.

**Not started, and not to be started.** Confirmed 2026-09-17: there is parallel work in
flight, so the engine waits for an explicit go. What this spec does in the meantime is
remove the blocker on `cf_engine/schema/fields.py` — `docs/CF-CHUNK0-BUILD-SPEC.md` deferred
the submission shape "until the field set is known from more than one coverage", and it now
is, for class-rated Building and Personal Property.

---

## Where this is wired in

So the work is found by whoever picks up the harness build rather than living in a folder
nobody opens:

| Surface | What points here |
|---|---|
| `STC_Corpus_Index.xlsx` (repo root) | the 921-payload index itself |
| `docs/CF-CHUNK0-BUILD-SPEC.md` | `cf_engine/schema/fields.py` row — deferral reason retired, links to the spec. Territory-resolver finding confirmed from STC |
| `docs/CF-PROPERTY-BUILD-ORDER.md` | "What is already done, and worth not redoing" — spec, tracker and the STC corpus added as assets for chunks 1, 2 and 4 |
| `README.md` | index table |
| `CF_Algorithm/BUILD-LOG.md` | dated entry |
