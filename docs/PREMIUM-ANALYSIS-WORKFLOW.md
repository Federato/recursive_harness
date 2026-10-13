# Premium analysis — standing workflow

**Read this first whenever premium analysis is requested.** It records the method, what is
already built, the structure of ISO's premium model in both lines, and the traps that have
already produced wrong answers.

**Opened 2026-09-17**, from the GL and CF premium mapping done that day.

---

## 0 · The standing rule

> **Every premium analysis request gets a full ERC review at maximum granularity.**
> Never answer from one search axis.

This exists because *"does ISO produce a total by coverage?"* was answered **"no"** from a
search over datadef field names. It was wrong. The per-coverage totals exist as **rules** that
return values without writing any field, so a field-name search cannot see them.

**Check every carrier of meaning, every time:**

| Axis | How |
|---|---|
| datadef fields **written** | `ToDataDef="X"` |
| datadef fields **read** | `FromDataDef="X"` and `FromDataDef=".../X"` |
| **rule names** | `<rul:Rule Name="X">` — a rule can compute and return a value that is never stored |
| rate + domain **tables** | including header-only ones |
| **gates** | `SetCoverageOnPolicyIndicator`, `Exist`/`NotExist`, `MetadataCodes` |
| **state packages** | not just countrywide |
| **editions** | where the question is time-sensitive |
| **spelling variants** | singular/plural, abbreviated, and the concept as well as the word |

A field that exists is not a field that is used. A value that is computed is not a value that
is stored. Neither is a value that reaches the total.

---

## 1 · What is already built — do not redo it

| Artefact | Covers |
|---|---|
| `GL_Algorithm/GL_Premium_Map.md` / `.xlsx` / `.html` | GL: 571 groups, every premium field, roll-up, §5 inert fields, §7 state overrides |
| `CF_Algorithm/CF_Premium_Map.md` / `.xlsx` / `.html` | CF: 881 groups, seven levels, §4 proration, §5 state rewrites |
| `GL_Premium_Tree.html`, `CF_Premium_Tree.html` | navigable trees, collapsible, jurisdiction selector |
| `GL_PremOps_Prods_Premium_Trace.md` | the two core GL coverages, rule by rule |
| `GL_Scenario_Premium_Buildup.md` | worked scenario — Prem/Ops, Products, Liquor, Med Pay, TRIA, minimums |
| `GL_Account_Premium_Bracket.html` | GL multi-location / multi-class roll-up drawn as a bracket |
| `CF_Account_Premium_Bracket.html` | CF equivalent — columns are **depth**, since Building/BI/Contents enter at 3/4/5 |
| `*_PlainEnglish.html` | ≤500-word prose companions |

**The scripts, all read-only, all reproducible:**

```bash
python scripts/premium/01_premium_map.py        --line GL|CF   # the xlsx map
python scripts/premium/02_premium_tree.py       --line GL|CF   # tree + state overlay -> JSON
python scripts/premium/03_premium_tree_html.py  --line GL|CF   # the navigable page
python scripts/premium/04_account_bracket.py                   # GL account bracket
python scripts/premium/05_cf_account_bracket.py                 # CF account bracket
python scripts/build_backlog_html.py <page>                    # render any MD companion
```

---

## 2 · ISO's premium model — the constants

Identical in GL and CF. Three rule names, and nothing else:

| Rule | GL | CF | Does |
|---|---|---|---|
| `SetPremium` | 322 | 546 | rate → dollars on one record |
| `SetPremiumIndicator` | 322 | 546 | did this record produce a premium |
| `CalculateTotalPremium` | 571 | 881 | collect upward one level |

**Rate and premium are separate phases.** Zero of the 322 GL `SetPremium` rules perform a table
lookup — the rating chain has already written `FinalRate`. `SetPremium` only converts:
`round(FinalRate × Exposure ÷ basis, 0)`. **`FinalRate` is the seam** between "wrong rate" and
"wrong exposure/basis".

**The leaf gate has two conditions:**
```
contribute Premium   if PremiumIndicator = 1 AND Premium ≠ 0
contribute 0         otherwise
```
A coverage rated to zero and a coverage never bought are indistinguishable in the total.

**The aggregator:**
```
ErcCalculatedTotalPremium = Σ each child's CalculateTotalPremium
```
Children are reached **two ways** — `ForEach` over `<X>Table` for repeating, `Locate` for
singleton. Handling only the first silently loses premium (19 families at the GL root).

**`ErcCalculatedTotalPremium` is written and never read** (GL 200 / 0, CF 261 / 0). Values pass
up as `RunRule` returns. Every stored subtotal is an output for the caller.

### Shape differs sharply between lines

| Depth | GL | CF |
|---|---|---|
| 1 | **419** | 45 |
| 4 | 7 | **304** |
| 5–7 | — | 341 |

GL is wide and shallow (endorsements price at policy level). CF is deep and narrow (premium
follows the property). Anything walking the tree must handle seven levels.

---

## 3 · Where totals by coverage do and do not exist

The roll-up aggregates by **record hierarchy**, never by coverage. Per-coverage totals exist
only in two places, both conditional:

| Where | What | Form | When |
|---|---|---|---|
| `GeneralLiabilityCompositeRating` | **12 rules** — `premOpsCoverageTotalPremium`, `prodsCompldOpsCoverageTotalPremium`, `liquorCoverageTotalPremium`, 3 terrorism, Owners&Contractors, Railroad, Snowplow, Canoes, 2 Product Withdrawal | rules returning values; only their sum is stored, as `TotalClassificationsPremium` | only `CompositeRating = "Yes"` |
| `…PremiumToReachMinCoverage` records | **4 stored fields** — `TotalCyberIncidentLiabilityPremium`, `TotalLossOfElectronicDataPremium`, `TotalUnmannedAircraftPremium`, `LimitedProductWithdrawalClassPremium` | real datadef fields | when that coverage is on — they exist to test a minimum |
| Prem/Ops, Products, Liquor, ordinary policy | **nothing** | — | never |
| **CF** `CommercialPropertyPostTRIACoverage` | `TotalStructurePremium`, `TotalPrsnlPropPremium`, `TotalBusnIncPremium`, `TotalSpecialPremium`, `TotalSpClBusnIncPremium` | real fields, written once / read once, local to the TRIA and disclosure records | whenever TRIA rates — **but they total `TerrorismPremium`, not coverage premium** |
| CF Building / Contents / BI premium | **nothing** | — | never |

**Do not mistake `AnnualBasicLimitsCoPremiumPremOps` / `…ProdCompldOps` for the answer.** They
are built from `BasicLimitPremium`, not `Premium` — basic-limits sums for statistical
reporting, a different quantity.

---

## 4 · What ISO does not compute at all

**One full-term premium at the effective date. Nothing transactional.** (OI-98.)

A 14-field block sits on every record and is written 0 / read 0 across all 52 GL and 48 CF
jurisdictions: `AnnualPremium`, `PolicyTermPremium`, `PriorPremium`, `ProRatedPremium`,
`ProRatedPriorPremium`, `ProRatedChangePremium`, `TotalProRatedChangePremium`, `ChangePremium`,
`EvaluatedPremium`, `OverridePremium`, `ProRateFactor`*, `ProRateIndicator`*,
`TermFactorIndicator`, `EarnedInFullIndicator`.

\* live in CF **only** where a coverage is intrinsically part-term — Vacancy Permit
(`ProRateFactor`), Peak Season (`ProRateIndicator`), Builders Risk reporting form
(`FormAnnualPremium`, `AnnualPremiumOfPrecedingReportingPeriod`).

**The line:** proration is ISO's when it is part of *what the coverage is*, and the policy
system's when it is a consequence of *when the transaction happened*.

**Minimum premium is half-built.** ISO files the minimum and provides
`…PremiumToReachMinCoverage` records that the roll-up **will** add — but nothing computes the
shortfall. `PremiumToReachMin` and `TotPremiumPriorToMin` are written 0 / read 0.

**Above the full-term number there is no oracle.** Every defect found so far was a
disagreement with ISO. A pro-rata delta cannot be confirmed or refuted by ISO because ISO does
not produce one.

---

## 5 · State packages

| | GL | CF |
|---|---|---|
| Groups whose `SetPremium` a state rewrites | **4** (all Terrorism) | **213** |
| Override instances | 12, 6 states | **479, 21 states** |
| Premium groups only in state packages | 457 | 223 |
| Empty-body (suppressing) premium overrides | **0** | **0** |

State-over-countrywide resolution is settled architecture (**N5**), so this changes nothing
about *how* a premium is computed. It is a **testing-breadth** number: a GL coverage proven in
one state is nearly proven everywhere; **a CF coverage is not.** Spend CF state test cases on
the contested formulas first — Spoilage (8 states), Outdoor Trees (7), Antennas (7),
PostTRIA (6).

Premium rules are **never deleted** by a state — unlike CF validation messages, where 316
countrywide rules are switched off by an empty override.

---

## 6 · Method for a new request

1. **Read §1.** If the artefact exists, extend it rather than rebuild.
2. **Scope the question to datadef groups**, then run `01_premium_map.py` and filter
   `RollUpTree` — `Path to account total` gives the chain in one lookup.
3. **Sweep all axes in §0** before answering any "does ISO have X" question.
4. **Trace rules, not names.** Read `SetPremium`, `CalculateTotalPremium`, the gate, and every
   `Set*` that writes a premium-shaped datadef on the groups in scope.
5. **Check the state layer** — at minimum, whether any state overrides the rules in scope.
6. **Verify before publishing:** arithmetic re-computed independently of the renderer; JSON
   parsed; tree reachability and cycles checked in Node; no external requests in any HTML.
7. **Label anything illustrative.** Placeholder amounts get a warning band. No fabricated
   premiums.

## 7 · Output conventions

- **MD + HTML** via `scripts/build_backlog_html.py`; add the page to its `PAGES` dict.
- **XLSX** for anything row-shaped — one table per file.
- **A ≤500-word plain-English companion**, prose only, when the audience is non-technical.
- **Interactive** work as self-contained HTML — embedded data, no CDN, light/dark aware. Prefer
  computed SVG over CSS for anything with connectors.
- Index in `README.md`; state limits explicitly in a closing section.

---

## 8 · Traps that have already cost a wrong answer

| Trap | Cost |
|---|---|
| Searching field names when the value is a **rule** | said ISO has no Prem/Ops total — it has twelve |
| `ForEach` only, ignoring `Locate` | 59 groups looked unreachable |
| `[A-Za-z]+` where group names contain **digits** | 18 more looked unreachable |
| Table **column name** ≠ datadef name (`OccupCategorySeverity` vs `OccupCategoryRiskSeverity`) | grep returned nothing; read as "unused" |
| Searching `Premium` and missing `ProRateFactor` | understated the inert block by 4 fields |
| Countrywide only | missed all state overrides; CF has 213 |
| `ProtectionClass` vs `ProtectClass` | wrong field in a payload, fails silently |
| Assuming a declared field is populated | 141 of 163 GL premium fields are never written |
