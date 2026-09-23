# Rater Simplifications — Backlog

Standing list of places where the Excel rater knowingly diverges from what ISO filed, because a
simpler build was chosen for now. These are **not** compliance gaps that were missed — each one was
seen, decided, and deferred. The point of this file is that they stay visible instead of becoming
invisible once the formula works.

One row per divergence. Retire a row by fixing it, not by deleting it.

---

## Feature set: separate endorsement records per datadef group

ERC files a **distinct exclusion record on each datadef group**. The rater currently reuses one
Yes/No input across groups, which means a risk cannot elect the exclusion on one coverage and not
the other. Same shape every time, so these are worth doing as one batch.

> **CORRECTED AND LARGELY CLOSED 2026-09-22 (R-5).** The three rows below describe
> **two** filed records per exclusion. ISO files **five** — one per coverage group:
> `…Exclusion` (Structure) · `…ExclusionPrsnlProp` · `…ExclusionBusnIncome` ·
> `…ExclusionSpecialClass` · `…ExclusionSpclClassBusnIncome`. Verified directly in
> `CFCW20260601V01\Rules` for all three perils. That is **15 records driven by 6
> inputs**, not 6 driven by 3.
>
> **R-5 added 15 per-group inputs**, each defaulting to its master so current
> behaviour is unchanged, and rewired 17 of the 23 consuming rows. **Fully live for
> Special Class and SC Business Income; partial for Building / Contents / Business
> Income**, because six consumers route through shared `CALC - CoreScratchpad`
> helpers (and one cross-sheet reference that looks like a defect) which were left on
> the master rather than assigned to a group on a guess. See
> `CF_R5_Implementation_Record.md`.

| # | Coverage | Filed records | What the rater does | What breaks |
|---|---|---|---|---|
| S-1 | Special Class Business Income — **Vandalism** | `CommercialPropertyVandalismExclusion` on the Special Class item **and** `CommercialPropertyVandalismExclusionSpclClassBusnIncome` on the Business Income group | Reuses `'Special Class Inputs'!C26` for both | A risk cannot exclude vandalism on Business Income but not on the building, or the reverse |
| S-2 | Special Class Business Income — **Windstorm/Hail** | `CommercialPropertyWindstormOrHailExclusionSpecialClass` on the item **and** `CommercialPropertyWindstormOrHailExclusionSpclClassBusnIncome` on the Business Income group | Business Income points at the Special Class building's `WindstormOrHailExclFactor` cell | Same: one record drives both. Building excluded ⇒ Business Income excluded, whether or not it was elected. Decided 2026-09-16 — point for now. |
| S-3 | Special Class Business Income — **Theft** | `CommercialPropertyTheftExclusionSpecialClass` on the item **and** `CommercialPropertyTheftExclusionSpclClassBusnIncome` on the Business Income group | Not yet built — logged before it is | Same split. Found 2026-09-16 while tracing Special; the factor tables also differ (0.88 building vs 0.86 Business Income), so this one cannot be pointed even if the gate were shared. |

**Why S-1 and S-2 are safe enough today.** In both of those the *lookup* genuinely is shared — same matrix, same
key, and Business Income reads the key (`BasicGroupIISymbol` / class code) off the building item
anyway. Only the **gate** differs. So the pointed-at value is correct whenever both records agree,
which is the common submission.

**How to fix, when it is worth doing.** Keep the shared lookup block; give each group its own Yes/No
input and wrap the shared lookup in its own `IF`. The table data does not change — only the gate
does. Cheap per coverage; the cost is input-sheet real estate, which is why it is deferred.

**Where else to check before calling this batch done.** The same two-record pattern very likely
exists for the other exclusions and the other Business Income groups (plain Business Income has its
own `...BusnIncome` records too). Sweep the `Exist AtInputDataDef=` gates in each
`*Rules.Rule.xml` rather than assuming this list is complete.

---

## Feature set: known-inaccurate data shortcuts

| # | Item | What the rater does | What breaks |
|---|---|---|---|
| D-1 | CF BGI District-split states (AK, CA, NY) | NY uses a built shortcut; AK uses a ZIP mapping | Both are known-inaccurate, not production-ready |
| D-1a | **FIXED 2026-09-23 (Schedule O / P + `TBL - AKRatingArea`; ISO-verified in District I and II).** Alaska: how ISO actually picks the district (traced 2026-09-22 against live ISO) | The rater derives District I/II from the **ZIP** (`TBL - BGI Territories` K:M) | ISO never reads a District field in AK. It uses **`City` = ISO rating area** (Bristol Bay, Gateway, Greater Anchorage Area, Greater Juneau, Greater Sitka, Kenai Peninsula, Kodiak Island, Matanuska Susitna, North Star, Remainder of State) + **`BasicGroupIDistrictTerritory` Yes/No** (Remainder of State only) → `RatingTerrGroupICodeAK` → **District I = Gateway, Greater Juneau, Greater Sitka, or Remainder of State + Yes**; everything else District II. **The rater has no input for either**, so a ZIP-derived district can simply be the wrong answer: item 3 (Haines, 99827) is District I in the rater, and ISO needs the area to agree. Worth ~16% of Group I. **Fix direction (your call):** add an AK "ISO rating area" + Yes/No input on the Schedule and derive the district from it, as ISO does. Until then the payload reproduces the rater's ZIP-derived district, and AK Group I matches ISO exactly |
| W-16 | **FIXED 2026-09-23.** BI Group I small gap, all three states | Excel below ISO: AK -9, FL -7, CA -1 | Two causes: BI row 10 rounded once where ISO rounds three times; BI borrowed the **Building's** Cyber exceptions factor (0.997) where ISO uses Business Income's own (1.0 at Full Limit). Now AK 541 = CA 252 = ISO. See `CF_W16_W20_W21_Record.md` | Yes, small |
| D-2 | **Full insurable value** — `FullBldgValue` / `FullSpecialClassValue` | The rater has **no value input at all** — `Building Limit`, `Contents Limit`, `Business Income Limit` and `Special Class Building Limit` exist; no value field does. It therefore assumes **limit = value**, i.e. 100% insurance-to-value | Any coinsurance test that depends on the real insurable value. ISO keeps the two apart deliberately (its own AL sample: `Limit` 500,000 vs `FullBldgValue` 550,000). **Not** the same as `CoreScratchpad!B138 "TOTAL LIMIT"`, which sums Building + Contents *limits* for the DeductibleFactor lookup — adjacent figure, different consumer. Found 2026-09-22 while specifying the payload generator |

**On D-2, and why the payload generator reproduces it rather than fixing it.** The generator sets
`FullBldgValue = Limit`. That is deliberate: the payload must reproduce the rater's assumptions exactly,
so that a three-way diff (Excel vs ISO vs engine) surfaces *real* defects. Supplying a truer value in the
payload than the workbook holds would manufacture a disagreement caused by the generator, not by the
rater. **Fix the rater first — add the input rows — then the payload follows.** Until then the only
observed consumer of the field is ISO's "Full Value cannot be lower than the Limit" validation, which
equality satisfies; a rate effect is not ruled out, merely not demonstrated.

---

*Added 2026-09-16. Source for S-1: `Excel_Rater_SpecialClassBusinessIncome_VandalismExclFactor_Formulas.html`,
step 6. Source for S-2 and S-3: `CommercialPropertySpecialClassRules.Rule.xml` and
`CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` — `SetWindstormOrHailExclFactor` and
`SetSpecialTheftExclusionIndicator` in each.*

---

## Feature set: filed multipliers the rater does not apply

| # | Coverage | Status | Detail |
|---|---|---|---|
| M-1 | **Special Class** and **Special Class Business Income** | ✅ **CLOSED 2026-09-22** | IRPM / PackageMod / MultiPremium now reach both. 240 cells repointed at the R-4 inputs; verified premiums unchanged at 1.0 and moving at 0.9 (SC $1,434→$1,292, SCBI $406→$365) |

### Correction — M-1 was originally filed on a false premise

This entry first read *"`Special Class Worksheet` has no such cells at all — only
`LCM`"*, and concluded that wiring them in meant **new rating behaviour** whose premium
impact needed the user's approval.

**That was wrong.** The sheet has **24** such rows and the premium formulas already
consume them — `=ROUND((C15/100)*C16*C17*C18*C19*C20*C21,0)`, where C17/C18/C19 *are*
the three factors. The R-4 survey matched the **abbreviated** labels the
Building/Contents/BI sheets use (`IRPM`, `PackageMod`, `MultiPremiumDispersion`) while
this sheet uses ISO's **full** names (`IRPMFactor`, `PackageModFactor`,
`MultiPremiumAndDispersionCreditFactor`). A clean result that was really an empty
search — the same defect shape the harness repeatedly found in its own instruments.

So it was never new rating behaviour: it was **the same disconnected-constant defect in
a third place.** Rows 17/18/19 held the formula `=1`, and all eight blocks chained off
them.

**Standing lesson:** when a survey reports a factor *absent* from one sheet but present
on its siblings, suspect the label vocabulary before believing the absence. Read the
sheet and report what is there, rather than asking whether a guessed label exists.

### A real bug found while fixing it — row 82

`MultiPremiumAndDispersionCreditFactor` at row 82 read **`=C60`**, which is
*PackageModFactor*, instead of `=C61`. Special Class's **Special** form therefore
counted PackageMod twice and ignored MultiPremium entirely. Invisible while both sit at
1.0; wrong the moment they differ.

**Fixed by removing the chain, not repairing the link.** All 24 rows now reference the
named inputs directly. A chain already wrong in one place will be wrong again after the
next copy-paste; direct reference makes every block independently correct and retires
the whole class of bug.

---

## Feature set: totals and rollups

| # | Item | What the rater does | What breaks |
|---|---|---|---|
| T-1 | **`Total Premium` omits two coverages** | `'Policy Inputs'!I9` is `=I3+I4+I5` — Building + Contents + Business Income only. It excludes **I6 Special Class Building** and **I7 Special Class Business Income**, both of which it displays directly above it | On the current sample the headline total reads **$17,904** when the five coverages sum to **$19,744** — understated by **$1,840, about 9.3%**. Almost certainly because the Special Class rows were added later (BUILD-LOG Entry 33, 2026-09-14) and the total was never extended. **Not a judgement call about ISO's rules — a cell labelled "Total Premium" that omits two of the five premiums above it is wrong on its own terms.** Found 2026-09-22 while closing M-1; **not fixed**, because it changes the headline number the user reads and that should be a deliberate act |

---

## Feature set: filed rules that produce a zero instead of a neutral value

Places where a missing input drives a factor to `0.0` rather than `1.0`, so the premium collapses to
nothing rather than simply not receiving a credit. **These are ISO's filed behaviour, not our
simplifications** — they are logged here so the rater reproduces them deliberately, with a visible check
cell, instead of someone "fixing" them later and quietly changing the premium.

| # | Where | Trigger | Result |
|---|---|---|---|
| Z-1 | Legal Liability, Building and Personal Property | `AddlInsurableIntOption` left **blank**, or no Legal Liability Coverage Form record at all | `LegalLiabAddlInsurableIntFactor = 0.0`, multiplied unconditionally &rarr; **premium of zero**. **Corrected 2026-09-16:** `Option4` *is* "None" and returns 1.00, so a risk with no additional insurable interest is meant to be coded Option4 and gets a neutral factor. This is therefore a **mandatory input** once Legal Liability is selected, not an unfortunate default. Build it as a required field with all four options; keep a check cell for the blank case. |
| Z-2 | Special Class Business Income, vandalism | gate passes but ClassCode is blank | `VandalismExclFactor = 0.0` &rarr; zero rate |
| Z-3 | Business Income, educational institutions | `TypeOfRisk = "Educational Institutions"` with no Changes-Educational-Institutions endorsement or null month count | `ChangesEducationalInstitutionsExtensionOfRecoveryFactor = 0.0`, which makes `TypeOfRiskFactor` zero and drives the BGI/BGII final rate to zero |

**How to apply:** reproduce the `0.0` exactly. Add a check cell that flags a zero factor so it is visible
rather than silent. Do not substitute `1.0` without a circular check confirming ISO's intent.

---

## Feature set: wiring defects found during the R-8 Contents migration

**Logged 2026-09-22.** Unlike the rest of this file, these are **suspected defects, not chosen
simplifications**: each is a formula reading an input that looks like the wrong one. They were found
while R-8 Phase 2b-ii rewrote `CALC - Contents Rating` (`CF_R8_Phase2b_Record.md`). The migration
**preserved each one exactly** so Gate 1 stayed premium-neutral. **None is fixed**, because each
would change a premium. Every one needs checking against the ISO rule file before it's fixed.

| # | Where | What the rater does | What breaks | Premium today? |
|---|---|---|---|---|
| W-1 | Contents rows **76** (Broad) and **104** (Special): `LegalLiabAddlInsurableIntFactor` | Tests `IN - Location` row **33** (OccupSeverity) and row **61** (Construction Description) for `"Legal Liability Coverage Form"`; neither can ever hold that value. The sibling rows 25 and 53 (BGI/BGII) test row **10** (Coverage Form) | The Additional Insurable Interest factor **never applies to Broad or Special Contents** on a Legal Liability risk | **Yes**: item 1 (Legal Liability, Special) gets factor 1 where the BGI/BGII rows would apply the Option 1 factor |
| W-2 | Contents row **24**: `LegalLiabFactor` | Before R-8, column C tested row 10 (Coverage Form) and columns D–L tested row 8 (Building Coverage Type, `"Legal Liability"`). R-8 templated all 40 columns from column C | Resolved in practice. Logged so nobody assumes the D–L version was intended | No (same values on today's risk) |
| W-3 | Contents row **46**: `BGIIDeductibleByLocationFactor` | Reads `CALC - Bldg Rating` row 49, which gates on the **Building** wind/hail election (`IN - Location` row 96) | Contents gets or loses the 0.995 credit based on the Building's exclusion, not its own (row 97). ISO's PP rule reads `WindstormHailIndicatorPrsnlProp` | No: neutral while Per Location Deductible = No |
| W-4 | Business Income, all forms that borrow the building's rate | BI reuses the Building's computed rate, which (since R-5 closed) carries the **Building** wind/hail election. BI's own input (row 98) never reaches it | Excluding wind/hail on Building alone moves BI (R-8 test: **2699 → 1890**); excluding it on BI alone does nothing. Before R-5 BI followed the policy-level election | Only when the Building and BI elections differ |
| W-5 | Contents row **43**: BGII `CoinsuranceFactor` | Reads `CALC - Bldg Rating` row 46, the **Building's** coinsurance factor. BGI (row 15) looks up the Contents coinsurance | Wrong BGII Contents factor whenever Building and Contents coinsurance differ | Only when they differ (both 80% today) |
| W-6 | Special-form Contents deductible: CoreScratchpad rows **176–182** (now per-record copies on Contents) | Bands the deductible factor on the **record's own limit** | BGI and Broad band on the building/location TOTAL LIMIT, as ISO does. Special may be wrong the same way `DeductibleFactor` was before its fix | Possibly, on any Special risk whose contents limit and location total fall in different bands |

**How to work these.** Order by exposure: **W-1** and **W-4** first (W-1 moves today's premium,
W-4 moves it the moment the elections differ). For each one, grep the ISO rule file for the Set rule behind
the factor (`CommercialPropertyPersonalPropertyRules.Rule.xml` for W-1/3/5/6,
`...BusinessIncomeRules.Rule.xml` for W-4). Record the verdict here. Where the ERC confirms the
defect, fix it with the usual two-sided gate: unchanged where the fix should be neutral, moving where
it shouldn't be.

**Added 2026-09-22 during R-8 Phase 4** (`CF_R8_Phase4_Record.md`):

| # | Where | What the rater does | What breaks | Premium today? |
|---|---|---|---|---|
| W-7 | CoreScratchpad rows **57, 126, 216** (and the dead row 7): drag-fill drift | Columns D-L hold a different formula from column C: missing state prefix (57), table columns shifted one to the right (126, 216). Rows 9-12 had the same drift and were standardised in Phase 4a | Row 57: a County-keyed state in columns D-L can't resolve its BGII territory. Rows 126/216: items 2-10 read the wrong table column | No: none of these is live on today's risks. **Standing check that was missing:** a column-consistency audit (each column's formula = column C shifted) on every per-item sheet |
| W-8 | Special Class Group II base rate: `CALC - Special Class` rows 26/27 via CoreScratchpad **59/72** | Keys on **building k's** state + BGII territory + **construction symbol** | ISO keys `LookupBasicGroupIIRate` on the Special Class item's **own** `BasicGroupIISymbol`. Item 1's own symbol is **B**; the rater uses building 1's **AB** | **Yes, probably**: item 1's Group II rate (wind/hail exclusion is "No", so the lookup is live) |
| W-9 | `IN - Special Class` has **two SC Business Income limit inputs**: row 20 ("SC BI Limit", priced) and row 42 ("Business Income Limit", read by nothing) | Row 42 is dead. Phase 1's Schedule mirrored it by mistake; corrected in 4c to row 20 | A user who types the SC BI limit into row 42 changes nothing | No. **Resolved 2026-09-22 (R-8 Phase 5): `IN - Special Class` deleted; the Schedule carries one SC BI limit** |

| W-10 | Special Class protection class: CoreScratchpad 213 (Special Class code) via `IN - Schedule` SPECIAL CLASS.ProtClass | Prices the item on its **own** protection class | ISO's `CommercialPropertySpecialClass` carries **no** ProtectClass in any of 408 payloads; it inherits the Location's. Item 1 is **5**; its location's is **4** | **Probably**: item 1's Special Class base rate. Found 2026-09-22 building the payload map (R-8 Phase 6). Needs an ISO rule check, then a live probe like W-8's |

| W-11 | **Legal Liability item, FL: traced 2026-09-22, it splits into W-12 + W-13 + W-1** | Excel low against ISO (= engine): Building BGII 651 vs 999, Contents BGII 885 vs 1082, BI BGII 640 vs 862, Contents Special 191 vs 340 | The first hypothesis was wrong: the rater's Legal Liability branch already stops at the cause-of-loss adjustment, like ISO. The gaps are earlier in the chain (below). A ~0.8% residual on Building BGII (986 vs 999) is unexplained | see W-12 / W-13 / W-1 |
| W-12 | **Open Sides Group II symbol swap missing**: CoreScratchpad 59 / 72 (BGII rate keys) | Keys the Group II base rate on the building's own symbol even when `OpenSides = Yes` | ISO `SetBGIISymbolToUse` (CW 2023-08 and 2026-06): if OpenSides = Yes (or class 0580/0585/1300/1650/1150), the symbol is replaced via `LookupBasicGroupIISymbolAdditionalClasses` ("OpenSides" + construction code). FL item 1: AB → **B**, base 0.088 → **0.129**. Contents and BI Group II inherit it | **Yes**: every open-sided building. FL item 1 about -$770 across Building / Contents / BI |
| W-13 | **Roof surfacing factor applied in Florida**: Bldg Rating rows 9 / 40 | Applies the countrywide `LimitationsOnCovForRoofSurfacingFactor` (0.98 A and B; 0.9702 on Group II) in every state | **Florida files that table header-only** (`CF FL 20241201`), so ISO applies no factor in FL. The same overlay shape as NY's header-only symbol table | **Yes**: FL buildings with a roof limitation, ~2-3% on Group I/II |


| W-14 | **BI Group II after the open-sides symbol fix**: CALC - BI Rating rows 29-38 (borrow the building's Group II rate) | With W-12 in, BI BGII on FL item 1 is **937 vs ISO 862 (+75)**. It was 640 before W-12 | BI borrows the building's Group II rate, and ISO evidently carries only part of the symbol swap into BI (or applies a BI-specific factor the rater doesn't). Untraced | **Yes**, FL item 1 +$75 |
| W-15 | **Legal Liability Contents Special, residual** | After W-1: 239 vs ISO 340 (-101) | Untraced. Not the AII factor (W-1 applied it), and not the symbol (the Special chain doesn't use it) | **Yes**, FL item 1 -$101 |

> **W-10, W-18, W-19 FIXED 2026-09-22** (`120_w11_fixes.py --fix W10 / W18 / W19`, each verified on every
> ISO-rated state). **W-10:** the Special Class rate key uses the location's protection class (row 172). **W-18:**
> new Special Class row 221 `VandalismExclRate`; where a state files a rate (FL only), it is subtracted from the
> Group I rate and the factor is neutralised (rows 7 / 9). **W-19:** new `TBL - DeductibleByLocation` (per state;
> FL has none) replaces the hard-coded 0.995 in Bldg Rating 19 / 49 and Special Class 12 / 36. FL Special Class:
> BGI 875 → **738** (ISO 744), BGII 621 → 626 (631), Special 137 → 142 (144), SC BI BGI 216 → 188 (190). The
> residual is the Cyber factor ISO's FL filing can't apply. Premiums 21125 → **20970** (SC 1633 → 1506, SCBI
> 457 → 429).

| W-10+ | **Special Class protection class: CONFIRMED against live ISO 2026-09-22** | Keys the Special Class Group I base rate on the item's own class (5) | ISO keys on `ProtectionClassToUse`, the **location's** band ("1 to 4" from class 4): base 0.167 vs the rater's 0.189 | **Yes**: FL SC Group I and SC BI |
| W-18 | **Florida Special Class vandalism exclusion is a RATE, not a factor**: CALC - Special Class row 7 | Applies the countrywide ×0.95 factor in every state | Florida alone files `VandalismExclRate` (and empties `SetVandalismExclFactor`); ISO **subtracts** 0.016 from the Group I rate (0.167 − 0.016 = 0.151). The rater already does this for SC BI in FL (row 92), but not for the item itself | **Yes**: FL SC Group I |
| W-19 | **Florida has no deductible-by-location credit** | Applies 0.995 when Per Location / Deductible By Location = Yes (SC row 12; Bldg 19 / 49 / 99; the Contents and BI copies) | Florida alone files `DeductibleByLocationFactor` header-only; ISO applies no credit | **Yes**: FL SC today (item 1 elects it); FL buildings when elected |
| — | **Payload fixes, same trace** | — | Special Class `ClassCode` (an ISO input; its vandalism rule gates on it) and the deductible-by-location endorsement records (`…DeductiblesByLocationSpecialClass` / `…Bldg`) are now sent. Step 3 had them as "omit v1" or missing. ISO's FL SC Group I moved 821 → **744** once they were | — |

> **W-14 FIXED 2026-09-22** (`120_w11_fixes.py --fix W14` then `--fix W14R`, verified against live ISO). BI Group II
> RATE (row 33) was missing the **BCEG factor** that ISO applies (`BI BasicGroupIIRate` = base x LCM x numeric x
> BGIIBaseRateAdjustment x BCEG), and ISO **rounds the adjusted base before BCEG**. At Alaska's tiny rates the
> single ROUND gave 0.010 against ISO's 0.011. BI BGII: FL 937 → **855** (ISO 862, -7 = Cyber), AK 78 (ISO 79,
> the $1 family), CA 15 = 15. Premiums 21207 → **21125** (BI 2996 → 2914).

> **W-17, W-6, W-15 FIXED 2026-09-22** (`120_w11_fixes.py --fix W17 / W6`, verified against live ISO).
> **W-17 (new):** Contents Special RATE (row 88) left out the personal-property territory multiplier it had
> just computed (row 87). ISO: SpecialRate = base x LCM x PrsnlPropTerrMultiplier. **W-15** (FL LL contents
> Special -101) was this same omission (FL multiplier 1.397). **W-6:** Contents Special deductible now takes the
> parent building's Special factor (Bldg Rating row 100), because ISO copies `DeductibleFactorSpecial` down
> from the Structure. Result: Contents Special **CA 992 = ISO 992, AK 477 = 477, FL 335 vs 340 (-5 = Cyber)**.
> Premiums 20865 → **21207** (Contents 8254 → 8596).

> **W-1, W-12, W-13 FIXED 2026-09-22** (`scripts/cf/120_w11_fixes.py`, each verified against live ISO with
> `119_payload_three_way.py`). FL item 1 against ISO: Building BGII 651 → 983 (ISO 999), Contents BGII 885 → 1069
> (1082), Building BGI 511 → 521 (527), Contents Special 191 → 239 (340). The residual ~0.8% on each is the Cyber
> factor ISO's FL filing cannot apply. Premiums 19994 → **20865**. Record: `CF_W11_Fixes_Record.md`.

> **W-8 FIXED 2026-09-22 (R-8 Phase 4c, by decision).** ISO's use of the item's own symbol was confirmed live
> (`114_r8_sc_symbol_probe.py`: B 0.028 / AB 0.024). The isolation proof showed the symbol is the only
> change. Special Class 1434 → 1633, SC BI 406 → 457. See `CF_R8_Phase4_Record.md`.

---

## Feature set: rounding order and one-input-drives-every-group (2026-09-23)

Traced while closing W-16 (`CF_W16_W20_W21_Record.md`). After these, AK and CA match ISO on all 18 lines, and FL
matches on all 15 with Cyber off on both sides.

| # | Item | What the rater does | What ISO does | Status |
|---|---|---|---|---|
| W-20 | Legal Liability rate rounding: Building 32/62/86/112, Contents 30/58/81/109 | rate × LL × AII unrounded inside the premium | `ROUND(ROUND(rate × LL, 3) × AII, 3)`, then × limit | **FIXED 2026-09-23.** FL Building BGI 525 → 527 = ISO |
| W-21 | Cyber factors in the premium: every Building / Contents / BI / SC / SC BI premium row | base × Cyber × COLExcptns, one ROUND | rounds to the dollar after **each** Cyber factor | **FIXED 2026-09-23.** Was every $1 difference: AK Bldg BGII 99 → 100, AK Contents BGII 67 → 68, CA Contents BGI 3499 → 3498 |
| W-22 | IRPM / package mod / multi-premium rounding order | multiplies all three inside one ROUND | rounds after each, in an order that differs by coverage; BI and Legal Liability leave multi-premium out entirely | **Open, unverifiable today**: all three are 1.0 on every test risk, so ISO can't confirm a change. Revisit when a test risk carries an IRPM |
| S-4 | **Sprinkler leakage, one input for every group** | One sprinkler system and one exclusion on the Building; Contents and BI reuse the Building's rate (Contents row 10, BI row 11) | Contents reads the **occupancy's** own `SprinklerSystem` and needs `…SprinklerLeakageExclusionPrsnlProp`; BI needs `…SprinklerLeakageExclusionBusnIncome` | **Payload mirrors the rater** (`119`, 2026-09-23), as with D-2: occupancy sprinkler = building's; BI record sent when the building elects. A risk can't have different sprinkler facts per occupancy or group |
| S-5 | **Cyber: no Business Income / Extra Expense sublimit inputs** | `IN - Policy` holds only the property-damage sublimit and the aggregate | `CyberTypeOfLimitBusinessIncome` / `…ExtraExpense` = "Sublimit" when that limit is entered, which switches BI to the Sublimit factor row | BI is always "Full Limit" in the rater (W-16 hard-codes that row). Add the two inputs if a submission ever carries a Cyber BI limit |
| CY | **Cyber applied in FL / NY, where ISO files no Cyber factor** | Applied the countrywide 0.995 / 0.997 everywhere | FL and NY file both Cyber tables header-only; ISO can't rate Cyber there | **FIXED 2026-09-23 (user decision: drop).** `TBL - Cyber` per state, no rows for FL / NY. FL now matches ISO 15 / 15 with Cyber on |

## Feature set: New York (2026-09-23)

ISO does **not** refuse NY: the refusal was our payload leaving `CompletedBasicGroupIISymbol` blank (NY-only
`SetCompletedBldrsRiskBaseRate` then runs a Builders Risk lookup). NY's domain allows only "Not Applicable" for any
symbol but U; the payload now sends it, and **ISO rates NY; the engine matches 9 / 9**. What is left is Group I:

| # | Item | What the rater does | What ISO does | Impact (test risk: Brooklyn 11236, class 0311, constr 3) |
|---|---|---|---|---|
| D-1b | **FIXED 2026-09-23 (Schedule Q County).** NY district comes from the County, and the rater had no County | NY district = the Group I territory dropdown (Schedule G "New York City" → NYC table) | `RatingTerrGroupICode` from (City, County), falling back to (Remainder of State, County). **Bronx 030, Kings 240, New York 310, Queens 410, Richmond 430 → NYC table**, all else the plain table. The payload sends no County, so ISO used the plain table (0.083 vs 0.106) | Payload can't reproduce the rater without a County. Live ISO with County = Kings: NYC table, 0.106 = rater |
| W-23 | **FIXED 2026-09-23 (Bldg Rating 8).** NYC skips the protection-class factor (Class rating, territory 030 / 240 / 310 / 410 / 430) | Applies PC 0.92 in NYC | NY `SetProtectionClassFactor` (Structure and PersonalProperty): 1.0 in those five territories | **Yes.** With County = Kings, ISO 468 / 387 / 243 vs rater 437 / 360 / 224 (Bldg / Contents / BI Group I), ~+7% |
| D-1c | **NY Group I territory FACTOR still from the dropdown** | Schedule G (Group I territory label) → `TBL - BldgBGIRating` factor | ISO derives `BasicGroupIRatingTerrFactor` from the (City, County) territory code | Open. Matches on the test risk (1.0 both). Check whenever a NY city with its own code (Albany, Buffalo, …) is rated |
| — | Special Class in NYC | Special Class protection class not changed by W-23 | Not traced: no NY Special Class test risk | Open, unverified |

