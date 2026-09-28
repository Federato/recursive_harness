# Property chunk 19: task list and status

**Scheduled property items: nine families that put a specific thing on the policy
with its own limit.** Tasks set 2026-09-28, while chunk 18 is still open.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 19, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`900_chunk19_census.py`](../scripts/cf/900_chunk19_census.py), run 2026-09-28,
27 s, log `results/cf-raas/logs/chunk19_census.log`), which carries the three census checks from
chunks 15 and 17: messages in **every** rule file; each premium rule compared in **every
countrywide edition a state stands on**; messages searched by **form number and wording**, not
only by record name.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Order.** Chunk 18 closes first. Leased Property reads chunk 18's `AgreedValueFactor`, so C19-11
waits on C18-06.

**Status: TASKS SET 2026-09-28, 1 of 24** (the census). Next, once chunk 18 is gated: RC-1, C19-02.

---

## In plain English first

Each of these puts one specific thing on the policy with its own limit, priced at a
rate the build already has:
- **Tenants' Building Property / Glass**: a tenant insures the improvements or glass it owns in someone else's building (scheduled item by item, or unscheduled).
- **Radio or Television Antennas**: the antenna, and the income lost if it goes down.
- **Outdoor Trees, Shrubs and Plants**: landscaping, with a limit per item.
- **Outside Signs**: signs, rated differently for metal and other materials.
- **Brands and Labels**: pays to remove the insured's brand from salvaged goods.
- **Household Personal Property**: the contents of living quarters.
- **Leased Property**: property the insured leases from someone else.
- **Specified Property Temporarily Away**: named items while off the premises.
- **Manufacturers Consequential Loss**: stock made worthless because a matching part was damaged.

**57 of the 63 countrywide premium records have never been priced by ISO**, nor
have the 5 state-only glass records FL and MT file. The other 6 are
the unscheduled tenants' records (Group I, Group II and Special, for glass and for
other building property), which already match ISO on a stored policy. RC-1 starts
there: reproduce what ISO already priced before predicting what it hasn't.

## What the census found, before any task ran

| Family | Premium records | ISO has priced | Tables read directly (CW rows) | States that rewrite it | Messages (any file) | Editions |
|---|---|---|---|---|---|---|
| **Tenants' Building Property / Glass** (scheduled, unscheduled; glass, other than glass; 5 perils) | 20 + **5 state-only** (`BuildingGlassTenantsPolicyDetail…`, FL **and MT**, both in force) | **6** (unscheduled BGI / BGII / Special, both kinds) | the **Building** chain: BGI LOI (342), BGII LOI (57; AL GA NC SC TX), Broad base (30), `SpecialBuildingRate` (45 states), `DeductibleFactor` (240; 44 states), `BuildingGlassNoDeductibleFactor` (4; FL), `Deductible250Factor` (4) | AL KS NY RI (`SetPremium`); FL (on/off switches on the CW files); FL MT own glass files | 5: CP 14 01 with CP 14 02; detail pages needed / not applicable; Public Institutional Plan coinsurance 90 or 100% (AL KS RI) | same in all four |
| **Radio / TV Antennas** (property and BI) | 9 | 0 (on 1 fixture) | **30**: the **special-class** Group I rates (213; FL NY), BGII rate (45 states), 15 EQ sub-limit flat-deductible tables (FL files all) and the tier table (10 states), vandalism (161; FL GA KS NY), windstorm exclusion (8 states), own class code and BGII symbol (NY) | **46**, mostly the EQ sub-limit deductible tier lookup; formula rewrites in AL AR DC FL GA KS NY RI TX VT (+ CA NM SC EQ / wind) | 1: CP 14 50 not valid with coverage | same |
| **Outdoor Trees, Shrubs and Plants** | 4 | 0 | 12: special-class Group I rates, BGII rate, `VehExclFactorOutdoorTrees` (1; **CT MA ME NH RI VT**), vandalism, windstorm exclusion, own class / coverage / rating-ID codes, BGII symbol (NY) | **10**: AL AR DC FL GA KS NY RI TX VT (AR DC FL KS NY RI `SetPremium`) | 3: CP 14 30 not valid; per-item limits required; cause of loss must match the blanket page | same |
| **Outside Signs** | 5 | 0 (on 1 fixture) | **32**: as antennas, plus metal and other-than-metal BGII symbols (NY) and construction stat codes | **46**, mostly EQ sub-limit tiers; formula rewrites in AL AR DC FL GA KS NY RI TX VT (NY `SetPremium`) | 2: CP 14 40 not valid; NY construction vs sign description | same |
| **Brands and Labels** (CP 04 01) | 5 | 0 | `BrandsAndLabelsFactor` (1), `BrandsAndLabelsMaxIncrease` (1) | none | 2: CP 04 01 not valid with coverage form; deductible cannot be Not Applicable | same |
| **Household Personal Property** (CP 99 92) | 5 | 0 | `SpecialPrsnlPropRate` (45 states) | FL (residential rate lookup) | 3: habitational only; All Personal Property only; CT not with Standard Property Policy | same |
| **Leased Property** (CP 14 60) | 5 | 0 | `AgreedValueFactor` (1), **chunk 18's table** | none | 1, **found only by form**: CP 14 60 not valid with coverage form | same |
| **Property Temporarily Away** (CP 04 04) | 5 | 0 | `SpecifiedPropertyAwayFromPremisesAddlPremiumFactor` (7; FL) | FL (switches) | 0 | same |
| **Manufacturers Consequential Loss** (CP 99 02) | 5 | 0 | `ManufacturersConsequentialLossAssumptionFactor` (16) | FL (`SetPremium`) | 4: not valid with form / coverage type; minimum 80% coinsurance, ordinary and blanket | same |

No date arithmetic, no `Power`, no unregistered element anywhere in the chunk.

**What shapes the plan:**

1. **Three families price on the special-class rate chain, not Building's.** Antennas,
   Signs and Trees read `BasicGroupIRateSpecialClass` and their own class codes and
   Group II symbols (chunk 6's machinery). Tenants' reads the Building chain; Household,
   Brands, Leased, Temporarily Away and Manufacturers read the contents / personal
   property side. RC-1 resolves each on a real tree before any golden case.
2. **"46 states rewrite it" is mostly one mechanism.** Antennas and Signs are rewritten
   in every state, but in 33 (Antennas) and 35 (Signs) of them the only change is which earthquake sub-limit
   deductible tier table the detail record looks up (Tier 1 or Tier 2; FL files all 15
   flat-deductible tables). That is chunk 10's EQ layer; C19-17 proves it with probes where
   the tiers give different dollars. The genuine formula rewrites are ten states.
3. **Trees and Signs carry their own exclusions.** Trees has a vehicle-exclusion factor
   filed only in six New England states; both read vandalism (FL GA KS NY) and windstorm
   (8 states) exclusions, chunk 8's records.
4. **Editions are quiet.** Every premium rule is identical in all four countrywide
   editions, so RC-4 needs one MO probe, not an edition task per family.
5. **Leased Property borrows chunk 18's table.** Its premium reads `AgreedValueFactor`;
   its golden case follows C18-06 and must agree with it.
6. **Five state-only glass files, in two states.** FL and MT both file
   `BuildingGlassTenantsPolicyDetail…` (Group I, Group II, Broad, EQ, Special) plus their
   container, in every MT package back to 2020. The plan said "FL-only": MT is new. The
   census first missed all six because the name says `BuildingGlass`, not
   `BuildingProperty`; `166_` uses the same pattern, which is harmless there (it counts
   countrywide files only) but means the 5 are outside the 63. C19-18 prices them.
7. **A census bug found on the way.** The form-number search copied from `185_` held literal
   backspace characters where `\b` belonged, so it never matched a form in any rule file.
   Chunk 18's form hits came from its wording list alone. `900_` is fixed and also lists
   each family's forms explicitly: these families' files carry no form constants, and
   without the list Leased Property's CP 14 60 message was missed. Chunk 18's C18-13 should
   re-run its message census with the fix.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C19-01 | **Opening census**: population, formulas, tables, messages by record **and by form / wording** in every file, every edition, state layer, stored evidence, attach points, engine readiness | ✅ | **Done 2026-09-28** (`900_chunk19_census.py`, 27 s). Findings above: 63 countrywide premium records + 5 FL / MT glass records, 6 priced by ISO; 21 message rules; 10 states with formula rewrites (46 with the EQ tier lookup); identical in all four editions; no date nodes; no unregistered element |
| C19-02 | **The 6 records ISO already priced**: reproduce the unscheduled tenants' premiums on their stored policy, hand = engine = ISO, and which input turns scheduled vs unscheduled on. No new ISO calls | ⬜ | |
| C19-03 | **Attach map and switches**: every record's parent (the Detail containers, per-item limits, the BI record under Antennas), each container's own rules, every on-switch shape (FL's `SetCoverageOnPolicyIndicator`s), every blank-input default that zeroes a premium | ⬜ | gate 2 (with C19-05) |
| C19-04 | **Borrowed values**: every path to another record resolved on a real tree in its loop context: the special-class chain (Antennas, Signs, Trees), the Building chain (Tenants'), the personal property side (the other five), the blanket cause-of-loss match; hand = engine on every record | ⬜ | gate 6 |
| C19-05 | **Tables and literals**: every table's rows and key literals (own class codes, symbols, rating-ID codes, factors, the Brands max increase), and every state-filed table under any name (NY symbols, FL glass deductible and temporarily-away factor, the six vehicle-exclusion states, the EQ tier tables) | ⬜ | gates 2, 5 |

### RC-2 · Golden cases (7 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C19-06 | **Tenants' Building Property / Glass**: scheduled and unscheduled, glass and other than glass, all five perils; the glass deductible factors (none / $250) chosen to move a dollar; ISO live | ⬜ | gate 1 |
| C19-07 | **Radio / TV Antennas**: property on all five perils and the BI record; class code and Group II symbol looked up by hand; ISO live | ⬜ | |
| C19-08 | **Outdoor Trees**: per-item limits on all four perils, with and without the vehicle exclusion; ISO live | ⬜ | |
| C19-09 | **Outside Signs**: metal and other than metal (the symbol discriminated), all five perils; ISO live | ⬜ | |
| C19-10 | **Brands and Labels**: all five perils, one case where the max increase binds and one where it does not; ISO live | ⬜ | |
| C19-11 | **Household Personal Property and Leased Property**: Household on a habitational risk; Leased on `AgreedValueFactor`, agreeing with C18-06; ISO live | ⬜ | after C18-06 |
| C19-12 | **Temporarily Away and Manufacturers Consequential Loss**: two factor rows each, chosen so the row decides the dollar; ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C19-13 | **Zero cases**: each limit blank or zero; detail page present with no coverage and the reverse; scheduled item with no items; EQ rider without earthquake; each switch off; predict both readings, ISO live | ⬜ | gate 4 |
| C19-14 | **Messages**: all 21 (5 Tenants', 1 Antennas, 3 Trees, 2 Signs, 2 Brands, 3 Household, 1 Leased, 4 Manufacturers), each triggered and silent, the 80% coinsurance ones at 79 / 80; ISO live | ⬜ | gate 9 |
| C19-15 | **Shared names**: `Rate`, `Factor`, `LimitToUse`, the special-class rate fields, `BasicGroupIISymbol`, `CoinsuranceFactor`, `CoverageOnPolicyIndicator`, diffed rather than assumed; who writes each; whether a submitted value survives | ⬜ | gate 6 |
| C19-16 | **Exclusion records**: cyber-incident factors in every formula; vandalism, windstorm and Trees' vehicle exclusions (which record drives each), and the EQ sprinkler-leakage factor on Tenants' glass, each at a limit where the factor moves a dollar | ⬜ | gate 7 |

### RC-4 · States and editions (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C19-17 | **The EQ sub-limit deductible layer**: Antennas and Signs in Tier 1, Tier 2 and FL (flat-deductible tables) states, and the 10 that file their own tier table; probes where the tiers disagree; ISO live | ⬜ | |
| C19-18 | **The formula rewrites**: AL AR DC FL GA KS NY RI TX VT on Antennas, Signs and Trees; AL KS NY RI Tenants' and FL's switches; the Public Institutional Plan (AL KS RI); FL Household, Temporarily Away and Manufacturers; **the FL and MT state-only glass files** (5 each, diffed against each other); each predicted from the state's own rule and tables; ISO live | ⬜ | |
| C19-19 | **Editions**: all premium rules identical in the four editions; one MO (CW 2023 V02) probe and one each on a V03 and a V04 state to confirm | ⬜ | gate 8 |
| C19-20 | **All 46 states**: every family on every state's own package, predicted per state; ISO live | ⬜ | gate 3 |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C19-21 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; terrorism; stat codes (the construction and no-construction stat codes Signs and Antennas read); ISO live | ⬜ | |
| C19-22 | **Regression**: add the chunk 19 scripts and pin the golden figures; full run CLEAN for chunks 0–19 (`--jobs 4`); `157_ --all` | ⬜ | |
| C19-23 | **Census close**: count the nine families as built in `166_` (406 → 469 of 546, 86%) | ⬜ | |
| C19-24 | **File `CF-CHUNK19-GATE.md`** | ⬜ | 63 countrywide premium files |
