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
| W-7 | **CLOSED 2026-09-23 (RC-1): rows 7 / 126 are dead (no readers), 57 / 216 empty. The real defect was W-24.** CoreScratchpad rows **57, 126, 216** (and the dead row 7): drag-fill drift | Columns D-L hold a different formula from column C: missing state prefix (57), table columns shifted one to the right (126, 216). Rows 9-12 had the same drift and were standardised in Phase 4a | Row 57: a County-keyed state in columns D-L can't resolve its BGII territory. Rows 126/216: items 2-10 read the wrong table column | No: none of these is live on today's risks. **Standing check that was missing:** a column-consistency audit (each column's formula = column C shifted) on every per-item sheet |
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
| W-22b | **FIXED 2026-09-24 (`124 --fix W22`, ISO-verified).** IRPM / package mod / MPD | 800 premium cells now follow ISO's `SetPremium` per coverage x group: one round (Bldg BGI/BGII/Broad), chain PM -> MPD -> IRPM (Bldg Special, Contents, Special Class; Contents Special rounds rate x limit to 3 dp first), no MPD (BI, SC BI, Legal Liability). **Payload** also fixed: ISO reads PackageMod at POLICY level (Contents / BI / SC BI) and MPD on the PersonalProperty record (Special: policy level) -- both were only on the Structure, so ISO silently used 1.0 | Probe `scenarios/rc4/mods_irpm_pm_mpd.json` (IRPM 0.9, PM 0.95, MPD 0.97, 4 states): Excel = ISO 42 / 42 (was 9 / 42). Baseline 21171 unchanged. **Engine gap logged (ENG-FL-MOD):** cf_engine ignores all three modifiers in FL only (NY / AK / CA fine) |
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
| CY-NY | **FIXED 2026-09-23 (RC-1).** Correction to CY: New York DOES rate Cyber | CY gave NY no Cyber at all (no `TBL - Cyber` rows) and the payload drops NY's Cyber records | NY overrides the Cyber rules: exclusion factor **1.0**; exceptions factor from its own `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactorNY` = **1.005** on Group I / II / Broad / Special, property and BI / Extra Expense. Live ISO rates NY with both records. Only FL is a real gap (`ISO_Filing_Gap_FL_Cyber.md`) | **Open, needs Excel.** Add NY rows to `TBL - Cyber` (exclusion 1.0; exceptions 1.005 on the four groups); payload stops dropping NY. The 42 / 42 hid it because both sides dropped Cyber |
| ED-FL | **Local FL snapshot is behind live ISO** | `TBL - Editions` and the disk hold `CF FL 20241201 V01` | Live ISO rates on **CF FL 20241201 V02** (named in its error text, 2026-09-23) | Open: obtain V02, diff it (overlay-aware) before trusting FL tables |
| W-24 | **FIXED 2026-09-23 (RC-1). R-8's 10 → 40 widening missed 7 live CoreScratchpad rows** (140, 173, 180, 181, 208, 210, 211) | Records 11-40 read blanks: Contents BGI deductible 0, Contents Special base 0, BI Special base / theft 0 → $0 premiums | Found by the column audit + clone test; rows filled to AP. Standing check: `scripts/cf/136_column_consistency_audit.py --strict` | No premium today (only 4 records) |
| FL-BGII | **FL Group II territory is county-driven in ISO** (`DomainBasicGroupIIRatingTerrFL`) | RC-1 gave FL a plain 6-value dropdown (it had none) | ISO narrows the choice by county, as with NY | Open (RC-3, with a FL county input) |

## Feature set: RC-4 "more states" findings (2026-09-23)

| # | Item | Status |
|---|---|---|
| SCDED / SCSPB / SCFIN / SCTHEFT / W-25 / W-26 | Special Class deductible, base-rate edition, final rounding, theft factor; Group II rounding and roof split; single-row roof tables | **FIXED 2026-09-23** (`CF_W16_W20_W21_Record.md`, RC-4) |
| AZ-PFD | Arizona Private Fire Department Credit (location, 0.5-1) | Payload sends 1.0; **input missing (RC-3)** |
| WH-CO | CO / IN / OK county-driven wind hazard level territory; ISO refuses without it | **Input missing (RC-3)** |
| EQT-SC | SC requires an earthquake territory even without EQ cover | **Input missing (RC-3 / RC-5 Earthquake)** |
| ED-ALL | Per-state tables must come from the package in force on the effective date (`state_file_in_force`), not the newest on disk | **Audited 2026-09-24** (read-only; pyxlsb + one read-only formula dump). 13 states have future packages on disk (AK AL CA CT IA MA MD MO NC ND NJ NM NV). Keyed row-by-row check of every rated table they change (Group I / District I-II / Group II / Lowest Group II / territory factor / Special Building + PersProp / LOI / vacancy): **all in force** except ED-CA-SC. Full 47-state sweep of every `StateCode` block against the in-force file found ED-WHX. Limit: blocks with custom headers (`State`, `Ded.`) were checked for the changed tables only |
| CA-D2 | **CLOSED 2026-09-24, ISO-verified.** CA District II | District II base 0.090 vs I 0.069; probe `scenarios/rc4/ca_district_ii.json` 9 / 9 | n/a | Closed |
| ED-CA-SC | **FIXED 2026-09-24 (`124 --fix EDCASC`, ISO-verified).** CA Special Class deductible / wind-hail tables were from the FUTURE CA filing; plus two wiring bugs found by the probe | (1) `TBL - Special Class` BA:BE, CA:CE, BK:BO CA rows -> CW (in force). (2) Special Class Schedule rows 220-229 defaults were shifted (Deductible = policy THEFT ded, WindHail = Deductible, Theft = WindHail) -> C8 / C9 / C10. (3) SC Special deductible (rows 191 / 194) always used TheftDed; ISO uses it only when theft is covered and it differs | Probe `scenarios/rc4/ca_special_class.json` (CA, $150k, $1,000 ded, 1% W/H): before SC BGII 17 vs ISO 15, SC Special **0 vs 32**; after 24 / 24. Baseline 21171 unchanged, 42 / 42. Payload: deductibles now always sent as text (`ded_text`), ISO refused floats |
| ED-WHX | **Seven states switch OFF the countrywide wind/hail exclusion factor; the rater still applies it** | `CALC - Bldg Rating` 44 and `CALC - Contents Rating` 41 look up `TBL - ContentsTables` DL:DP; AR DC FL KS NY RI TX carry CW 0.35 / 0.315 | Those states override `SetWindstormOrHailExclFactor` (Structure and PersonalProperty) with an empty rule and file the table header-only. KS / FL use a replacement rate (`BasicGroupIIWindstormOrHailExclRate`, KS 0.023); TX its own factor (`WindstormOrHailExclFactorTX`, 0.1); AR / DC / NY / RI none found yet | Open, premium-changing only when a building / contents excludes wind/hail (none of today's test risks do). Trace per state with RC-2's W-4, then probe |
| ENG-FL-MOD | **CLOSED 2026-09-24 (FL V02 on disk).** cf_engine: FL premiums ignored IRPM / PM / MPD | n/a | ISO applies them in FL | Open, harness side. Found by the W-22 probe 2026-09-24 |
| ED-DEAD | `TBL - Special Class` AD:AI (Group II rate list) holds in-force AND future rows for the same keys | Nothing reads it (no formula, no defined name) | n/a | Clean-up only; no premium |
| NH-COS | **CLOSED 2026-09-24, ISO-verified.** NH cosmetic roof factor | Reading confirmed: NH applies ACV 0.98 on any paragraph, no cosmetic factor (the rater already did, W-26). The probe (`scenarios/rc4/nh_roof_paragraph_b.json`) found a ROUNDING gap instead -> **ROOFRND** (`124 --fix ROOFRND`): Bldg rows 10 / 72 / 95 now round after the roof ACV factor as ISO `SetBasicGroupIRate` / `SetAdjustedBroadRate` / `SetSpecialCauseOfLossAdjustment` do. NH Building Group I 1932 -> 1881 = ISO; 9 / 9. Baseline unchanged |
| TH-DED | **FIXED 2026-09-24 (`124 --fix THDED`, ISO-verified).** Theft deductible | The live rater had NO theft-deductible logic (Contents 160-165 were dead). New CoreScratchpad 127-131: ISO's Special-incl-theft total, theft lookup (Other Cause Of Loss), gate (theft covered, TheftDed not ''/NA/250 and <> Deductible), $250 branch. Bldg row 100 and Contents row 97 use them; Contents checks its own theft exclusion. Payload: occupancy `TheftDeductible` = building's; CP 03 20 `[{}]` when theft / dollar W-H ded differs (as ISO's STC payloads) | Probe `scenarios/rc4/ca_theft_deductible.json` (CA, theft covered, $5,000 theft vs $2,500): factor 0.84 vs regular 0.89, 9 / 9 = ISO. Not modelled: Special Class in the theft total. Baseline unchanged |
| SC-GI-ST | **FIXED 2026-09-24 (`124 --fix SCGIST` + `SCGISTFL`, ISO-verified).** Special Class Group I rate was CW only | New `TBL - Special Class` EI:EJ (State|Description|PC -> rate) for NY and PR from their in-force tables; row 4 reads it first, falls back to CW (ISO's FirstNonNull). **NY** blanks `SetSpecialClassDescConvertedOption` (only state that does), so ISO priced Group I at **0** unless the option is SENT: payload now sends the rater's derived option (row 171) for NY items. **FL** removed again: live ISO runs FL V02 (not on disk), which maps the above-ground pool to Option29b2 = 0.556 (= CW); V01 swaps the two pool rates | Probes: `ny_special_class.json` (Artificial Turf NY 0.165; Option1a NY 0.43 vs CW 0.044 -> $778 vs ~$80) 18 / 18; `fl_special_class_pool.json` Excel = ISO. 'Special Class in NYC' closed: ISO computes the SC protection-class factor but never uses it. Open: NY option names like Option12b1 are unreachable through the CW map; engine uses FL V01 (ED-FL) |

## Feature set: RC-2 probes (2026-09-24, `scenarios/rc2/`, live ISO)

| Probe | Result | Finding |
|---|---|---|
| W-4a Building excludes W/H, BI does not (AK) | 9 / 9 | ISO's BI Group II uses its OWN base; matched only because AK has one territory (lowest = base). Rater BI row 29 = Bldg 36 + 37 switches BI to the Building's LOWEST base when the Building excludes -> wrong in multi-territory states. Re-probe in a multi-territory state |
| W-4b BI excludes, Building does not (AK) | BI BGII **79 vs ISO 37** | BI row 36 multiplies the BUILDING's exclusion factor (1 here). ISO BI: ROUND(ROUND(ROUND(lowest(Bldg symbol) x LCM) x BI's own W/H excl factor) x BuildersRisk) |
| W-5 Contents coinsurance 100%, Building 80% (AK) | Contents BGII **68 vs 60** | Contents row 43 = Building's factor. ISO: Contents' OWN coinsurance factor; flat 1.5 at 50 / 60 / 70% / None |
| W-3 per-location ded, Building excludes (AK) | 9 / 9 but not discriminating | Reframed: ISO's Group II per-location credit (0.995) ignores every W/H exclusion; gate = per-location record + `WindstormHailIndicator` = 0 (no 1% >= 100k, 2% >= 50k, 5% >= 20k). Rater Bldg 49 gates on the Building's exclusion (ISO 0.995, rater 1.0 here; hidden by rounding). Needs a large-limit probe |
| S-1 SC BI vandalism differs (FL) | 15 / 15 | Already own election. Closed |
| S-2 SC BI W/H differs (FL) | SC BI BGII **162 vs 2** | SC BI follows the SC item's election, not its own |
| S-3 SC BI theft differs (FL) | 15 / 15 | Already own election. Closed |
| ED-WHX Building excludes W/H (TX) | Bldg / BI BGII **0 vs 559 / 364** | Rater uses a 'lowest' rate TX does not file -> 0 |

**ED-WHX, state families for the Group II cause-of-loss adjustment when W/H is excluded** (Structure / PP / BI rules, in-force):
CW = ROUND chain lowest x LCM x ACV x cosmetic x W/H excl factor x StdPol. **AR, DC, NY, RI** = exclusion has no effect (regular
Group II rate x StdPol; RI public-institutional variant). **TX** = regular rate x `WindstormOrHailExclFactorTX` (0.1) x StdPol (Structure,
PP, BI). **FL** = `BasicGroupIIWindstormOrHailExclRate` x LCM x StdPol (BI: x numeric). **KS** = `BasicGroupIIWindstormOrHailExclRate` x LCM
(x ACV x cosmetic; BI x BGIIBaseRateAdjustmentFactor). NY Structure's rule is empty (to confirm by probe).

**RC-2 FIXED 2026-09-24** (`124 --fix W5 / S2 / WHX / WHXNUM / WHXNUM2 / W3FIN`, each gated premium-neutral, saved + reopened):
W-5 Contents Group II coinsurance = contents' own (flat 1.5 at 50/60/70%/None). S-2 SC BI Group II own base / numeric / exclusion.
ED-WHX new `TBL - WHExclMode` (AR DC NY RI NONE, TX 0.1, FL 0.001, KS 0.023; else CW) applied to Building / Contents / BI / SC / SC BI,
each on its OWN election; CoreScratchpad 68 forces numeric 1 only for an excluded CW-mode building (ISO's own rule). W-4 BI base is its
own lookup. W-3 Group II per-location credit = per-location record + NOT WindstormHailIndicator (no exclusion gate). FINRND final rates
round after the per-location credit (Bldg 22/52/76/102, Contents 20/48/71/99). All 14 RC-2 probes Excel = ISO; RC-4 probes still clean;
42-state regression 40 / 40 rated states, 0 mismatches; standard 42 / 42 at 21171. Closed: S-1, S-3 (already own). Still open: S-4
(sprinkler per occupancy -- needs an input, moved to RC-3); CW lowest-rate variants AL / CT / NH / WV / GA / KY / IN / VT differ only in
which roof factors they apply (not probed); Contents Broad / Special multiply a multi-res factor ISO's PP rule lacks (1 on every test).

## Feature set: RC-3 new inputs -- DONE 2026-09-24 (`scenarios/rc3/`, live ISO)

| Item | Fix | Proof |
|---|---|---|
| WH-CO / EQT-SC | `124 --fix RC3GEO`: Schedule R `WindHazardTerr` (CO / IN from County col Q, OK "Entire State") and S `EQTerr` (SC by ZIP, new `TBL - EQTerr` from DomainEQTerrSC); payload sends both. Neither moves a premium (hazard level feeds only Specific Group II eligibility messages; EQTerr feeds an EQ factor) | CO / IN / OK / SC now rate: **44 / 44 states, 0 refused** |
| AZ-PFD | `--fix AZPFD`: Schedule T `AZFireDeptCredit` (default 1); Group I base x credit on the Class path of Bldg / Contents / SC, as AZ `SetBasicGroupIRate`; payload sends it | credit 0.75: Bldg BGI 1170 -> 883, Contents 1021 -> 768, BI unchanged, all = ISO |
| D-1c | **No change**: ISO's NY territory factor keys on the territory INPUT (label), as the rater; City + County only pick the district table (D-1b) | Buffalo (0.71): 238 = ISO |
| D-2 | **No change**: full insurable value only feeds blanket / value-reporting rules; doubling every Full*Value moved no ISO premium (FL, AK). Moved to RC-5 Blanket | direct ISO re-rate |
| S-5 | `--fix S5`: IN - Policy F7 / F8 Cyber BI / Extra Expense sublimits; BI + SC BI Cyber exceptions factor picks Sublimit; payload sends CyberBusnIncomeCovLOI / CyberExtraExpenseCovLOI | CA BI 252 -> 251, AK EE 541 -> 539, = ISO |
| S-4 | `--fix S4`: occupancy J SprinklerSystem, Contents Q / BI Q SprinklerLeakageExcl (default = building's); Contents 10 / BI 11 own rates; payload per record | 3 probes, each coverage moves on its own election, = ISO |
| Linked SC | Payload only: UnitNumber on Location / Structure (as ISO's STC payloads) and SC `BuildingIDNumber`; the rater already linked | linked 58 vs unlinked 51 (BGI), both = ISO |

**FL-BGII DONE 2026-09-24** (`124 --fix FLBGII`, dropdowns only): new `TBL - Counties`; County (Q) lists the location state's counties (NY / FL / CO / IN, else Not Applicable -- it had accepted NY counties only, so FL / CO / IN could not pick one); FL Group II territory (I) offers only the county's territories (DomainBasicGroupIIRatingTerrFL, V02), all of FL's when no county. Verified after reopen: Bay -> Seacoast Zone 2 / 3; Monroe -> the two Monroe territories.
Tooling: `120 main` save now retries "call rejected"; scenario values that look like dates / numbers must be prefixed `'`.

## Feature set: RC-5 ED-FL -- CF FL 20241201 V02 (DONE 2026-09-24, `scenarios/rc5/`, live ISO)

V02 downloaded by the user into `ISO_ERC_Files/CF/20230801v4/`. It rides on **CF CW 20230801 V04** (not CW 2026), renumbers FL's
Special Class options, renames FL's descriptions to CW's, and adds vacancy codes 0581 / 0582. Fixes (`124 --fix`):
- **SCSTATE** (after EDFL / EDFL2 were refined by ISO refusals): a state-filed Special Class option map or rate table REPLACES CW
  inside the state's project -- ISO's "CW" fallback key is looked up in the state's table and fails. FL (own map + rates), NY (CW
  option sent, NY rates), PR (CW option, PR rates); anything else is #N/A = ISO refuses. Probes: above-ground pool 0.556 = ISO;
  in-ground pool PC 5+, Solar Panel Arrays (FL) and Bridges (NY, Option10a) -> ISO refuses, rater #N/A.
- **VACFL**: FL vacancy 0581 / 0582 (0.015). **SUBSTD**: the substandard-condition table lacked CA DC IL KY NJ NY FL UT (+ any
  CW state) -> added from each in-force package / CW (FL: CW V04). **FLRES**: FL Contents Special picks Residential by the
  OCCUPANCY category (FL `SetSpecialBaseRate`), not the building class. Probe `fl_vacant_0581.json` 15 / 15.
- **EDFLSTAMP**: TBL - Editions FL row -> V02 / CW 20230801 V04.
**ENG-FL-MOD closed**: with V02 on disk cf_engine applies IRPM / PM / MPD in FL (mods probe 42 / 42 all three).
Regression: 44 / 44 states, 0 refused, 0 mismatches; standard 42 / 42 at 21171.

**Specific / Tentative (2026-09-24, user correction):** the rater HAS Specific and Tentative Group I (Schedule G rating type, O input rate; CoreScratchpad 6 sends both
down the Specific path, as ISO's `SetBasicGroupIRate` does -- Specific and Tentative share it; Tentative only adds a form and stat codes).
Payload now sends `SpecificGroupIRate` for Tentative too (it sent it for Specific only). Probe `scenarios/rc5/fl_tentative.json`: 15 / 15.
Earlier notes calling Specific/Tentative "unbuilt" were wrong. Still missing: **Specific Group II** (RC-5).

**Specific Group II DONE 2026-09-24** (`124 --fix BGIISPEC`): CW has none; 36 in-force states add it (new `TBL - BGIISpecific`, variant STD / NY).
Schedule building AJ `BGIIRatingType` (Class / Specific, default Class) + AK `BGIISpecificRate`, Contents R `BGIISpecificRate`. Bldg 42 /
Contents 39: ROUND(ROUND(S x LCM) x BCEG) (NY: ROUND(S x LCM)); BI 33 uses the building's S: ROUND(ROUND(ROUND(S x LCM) x BCEG) x adj).
Election ignored where the state has no Specific Group II (AK AZ CA DC ME NV OR UT VT WV). Payload sends RatingTypeBasicGroupII /
SpecificGroupIIRate. Probes `scenarios/rc5/bgii_specific_*`: OH 1220/1088/107 -> 1119/615/98, NY 312/206/171 -> 190/91/108, AK unchanged,
all = ISO. Not modelled: AR / KY / OK wind-mitigation credit (1 without WCF inputs); Specific-eligibility messages (wind hazard level).

## Feature set: RC-5 Blanket -- Phase 1 DONE 2026-09-24 (Building Only, Average; `scenarios/rc5/blanket_*`, live ISO)

`124 --fix BLKT1 / BLKT1B / BLKT1C / BLKT1D`. New `IN - Blanket` (10 groups: ID, Type, Method, CauseOfLoss, Coinsurance, TotalLimit),
Schedule building AL IncludedInBlkt / AM BlktIDNum / AN FullBldgValue (D-2), new `CALC - Blanket` (per building: in-blanket flag,
group total full value, blanket LOI basis, four weights, blanket coinsurance factor 1 at 90% else 0.95, four average rates, share),
the building's LOI rows read the blanket basis, Building premiums use ISO's blanket formula. Payload: BlktRated "Yes" (ISO deletes
the record otherwise), MUBlktRated "No", CommercialPropertyBlanketRating / Detail, structure IncludedInBlkt / BlktIDNum / FullBldgValue.
Findings: (1) each state's package rides on a specific countrywide project -- CA / NC CW 20230801 V03, MO V02, FL IL MA NJ RI VT
V04, the rest CW 20260601 (`TBL - CWBase`); CW V01-V03 allocate the blanket premium by BlktProportion = ROUND(value / total, 2),
V04 / 2026 by the exact share. (2) Excel stores "90%" as 0.9. Probes: CA two buildings 12 / 12; OH 100% coinsurance 11 / 12 --
**known limitation**: Special on an exact .5 tie (ISO's double arithmetic gives 287.4999... and rounds down; Excel's ROUND treats it
as .5 and rounds up). Next: Phase 2 Contents (Personal Property Only; Building & PP Combined).
**Wider follow-up (not yet audited):** the 9 states on an older countrywide base may differ from CW 2026 elsewhere too; every standard
risk matches today.

**Blanket Phase 2 DONE 2026-09-24** (`124 --fix BLKT2`): Contents -- Personal Property Only and Building & PP Combined. Schedule Contents
S IncludedInBlkt / T BlktIDNum / U FullPrsnlPropValue; `CALC - Blanket` rows 21-38 (contents weights with the BUILDING's deductible
factors, Special pre-rounded with watchman / burglary credits); group totals and average rates add buildings and contents sharing the
ID; Contents row 117 (LOI basis) reads the blanket basis; Contents premiums on ISO's chain (PM -> MPD -> IRPM, ISO operand order).
Probes: CA Combined (2 buildings + contents) 12 / 12; OH PP Only 100% 9 / 9. Next: Phase 3 BI blankets.

**Blanket Phase 3 DONE 2026-09-24** (`124 --fix BLKT3 / BLKT3B`): Business Income (types BI With / Without Extra Expense). Schedule BI
R IncludedInBlkt / S BlktIDNum / T FullBusnIncomeValue; `CALC - Blanket` rows 41-58 (weights V x CoL adj x BI factor; Broad / Special
V x rate; no LOI, no deductible; average without coinsurance factor); group TotalFullValue now counts buildings, contents and BI
sharing the ID; BI premiums on ISO's blanket formulas (BGI / Broad / Special one round with IRPM x PM; BGII chain; no MPD). Finding:
a blanketed BI record's Type-of-Risk factor uses the BLANKET's coinsurance (ISO SetCoinsuranceToUse) -- BI rows 89 / 90.
Probes: CA two BI 15 / 15 (V03, rounded share); OH two BI 15 / 15 (2026, exact share). Next: Phase 4 (Special Class, Highest).

**Blanket Phase 4 DONE 2026-09-24 -- BLANKET COMPLETE** (`124 --fix BLKT4 / BLKT4B / BLKTDIAG`): Special Class (F InclInBlanket +
X BlktIDNum + Y FullSpecialClassValue) and SC BI (P / Q / R) in blankets; Building-type groups average Building + Contents + SC,
BI-type groups BI + SC BI; the **Highest** method on every section (unit rate = ROUND(weight without the value, 3) at the item's own
LOI; group rate = ROUND(MAX x coinsurance, 3); LOI basis = own value); SC premiums chain limit/100 x share x avg -> PM -> MPD -> IRPM,
SC BI one round. Finding: a blanketed SC BI record's factor uses the blanket's coinsurance (rows 207 / 208), as BI. Diagnostics row 16
now warns only on a blanket election without a valid ID. Probes: NY Combined with 2 SC items 18 / 18; NY BI + SC BI 18 / 18; CA
Highest 12 / 12; OH BI Highest 15 / 15; all Phase 1-3 probes unchanged; 11 state batches 42 / 42; standard 42 / 42 at 21171.
Not built: Builders Risk blanket type, value-reporting / multi-location average rates (MUBlktRated), agreed-value blanket variants.

## Feature set: Older-countrywide-base audit -- DONE 2026-09-24 (`scenarios/rc5/mo_sc_pool_v02`, `whpct_*`, `sptot_oh_sc`, live ISO)

Each state's package rides on a specific countrywide project (`TBL - CWBase`): CA / NC on CF CW 20230801 V03, MO on V02, FL IL MA
NJ RI VT on V04, the rest on CW 20260601. Tables and rules were diffed base by base against 2026.
- **V04:** identical to 2026 (tables and rating rules). No change.
- **Tables (`124 --fix SCBASE`):** V03 lacks one Special Class description ("Wind Towers..."); V02 has 9 renamed descriptions and
  swapped pool rates. `TBL - Special Class` EI:EJ carries CA / NC / MO from their own base; #N/A where ISO refuses.
- **Rules (`124 --fix CWRULES`):**
  (a) % wind/hail deductible (1% / 2% / 5%) factor and indicator are sized on WindstormOrHailTotAmtInsurance = building + its
  contents without a wind/hail exclusion + included Special Class items (2026 / V02 / V04), but on the building's limit alone on V03.
  The rater used the building limit everywhere (OH probe: 0.91 vs ISO 0.87). CS 90 / Bldg 49 now switch on the base.
  (b) V03 contents compute their own % wind/hail factor on their own limit (2026 copies the building's): Contents row 47.
  (c) V02 (MO): Specific Group I = ROUND(specific x LCM, 3), no roof ACV, one rounding (MO probe 508 vs ISO 522); excluded
  Group II lowest path without roof factors (Bldg rows 10 / 42).
- **Found along the way, every base (`124 --fix SPTOT`, `SCTOT`):**
  - The Special deductible factor was sized on the building limit; ISO uses SpecialTotAmtInsurance = building (blanket share if
    blanketed) + contents + Special Class items included in the building (CS 122; OH probe 0.92 vs ISO 0.96). Theft total
    (CS 127) and % wind/hail total now include the included Special Class items too.
  - CS 215 (included Special Class limit in the building's total) pointed at building 1 ($A$48) in every column and counted
    inactive / not-included items. Now per building, active, IncludedInBuilding = Yes.
  - The baseline never showed either: its buildings sit in the top bands and its Special Class item is not included in a building.
- **Probes:** OH % wind/hail 42 / 42; NC (V03) 42 / 42; MO (V02) 42 / 42; OH with an included Special Class item 42 / 42. All
  earlier probes unchanged (FL / NY refusal probes still refuse identically); standard 42 / 42 at 21171.
- **Simplification kept:** contents in the Special / theft / wind-hail totals use their scheduled limit, not a blanket share.

## Feature set: RC-5 Earthquake -- Phase 1 DONE 2026-09-24 (`124 --fix EQ1`; `scenarios/rc5eq/`, live ISO)

Building and Personal Property earthquake on **CP 10 40** (percentage deductible) and **CP 10 28** (flat-dollar
deductible), not in a blanket, not sprinkler-leakage-only. Trace: `Earthquake_Rater_Trace.md`.
- **Inputs:** Schedule location U `EQCauseOfLossForm` and V `EQTerrEntry` (S `EQTerr` now reads V outside SC); building
  AO `EQCovIndicator`, AP `EQClass`, AQ `EQDeductible`, AR `SoftStory`, AS `MasonryVeneer`; contents V `EQCovIndicator`,
  W `EQGrade`. EQ coinsurance = the item's coinsurance (ISO's domain forces it).
- **Tables:** `TBL - EQ` (22,315 keyed rows `PREFIX|STATE|keys`: loss costs, tier, height group / factor, BCEG, MO
  BCEG x territory, class group, soft story, sprinklered, veneer, coinsurance, <80% factor, builders risk, % deductible;
  plus dropdown lists and a per-state source list) and `TBL - EQFlatDed` (32,940 banded rows).
- **Calc:** `CALC - EQ` rows 1-39 building, 41-76 contents; `IN - Policy` I8 Earthquake premium (`OUT_Prem_EQ`) is in
  the total. Payload sends the EQ fields, the form record (CP 10 40 endorsement / CP 10 28 flat form) and, for contents,
  `FullPrsnlPropValue` (ISO's CP 10 28 deductible band only counts contents when it is sent).
- **Findings (live ISO):**
  1. **Table resolution:** ISO uses the state's package IN FORCE, else the countrywide base. An OLDER state package is
     never used (CA 20240401's veneer / soft-story files are ignored: CA rates soft story 1.42 from CW V03 and refuses
     CA's own "10% to 25%"). `state_file_in_force` (used by earlier fixes) walks back to older packages -- **audit it**.
  2. A blank SprinklerSystem (the Schedule's "Select" is not sent) applies the 1.06 sprinklered factor; a blank BCEG
     gives 0 and zeroes the EQ premium. The rater mirrors both.
- **Probes (all Excel = ISO = engine):** CA CP 10 28 (soft story 1.42, veneer 1.1, height 0.84) 1743 / 1096; CA CP 10 40
  20% 308 / 191; MO CP 10 28 (V02) 51 / 48; CA bands (BCEG 1.04, coins 90% 0.95, contents 70% x1.5, location total
  600,000 -> 1.426 not 1.383) 102 / 111; MO CP 10 40 territory 3A, BCEG 0.96 via V02 BCEGEQFactor 564 / 334.
- **Simplifications / not built:** contents in a YARD group use the building's BCEG factor (ISO: 1.0); BI, Special
  Class and SC BI earthquake; sprinkler-leakage-only; sub-limit forms CP 10 29 / 10 45; blanket EQ; TX deductible
  formula, CA limited EQ, roof-tank and public-institutional factors (Phase 4). The territory is typed (no per-state
  dropdown).
- **Found outside EQ (not fixed, user's call):** building coinsurance 90% -> Building Group II 18 vs ISO 21 (CA);
  contents coinsurance 70% -> Contents Group I 0 vs 535 and Special 0 vs 241 (CA).

## Coinsurance below 80% and adjusted-rate rounding -- DONE 2026-09-24 (`124 --fix COINS1`; `scenarios/coins/`, live ISO)

The baseline has every item at 80% coinsurance (factor 1.0), so neither bug ever showed.
1. **Rounding.** ISO rounds after the coinsurance factor, then after LOI: R3(R3(COL x Coins) x LOI). Contents Special
   also rounds after watchman and burglary. Bldg 18 / 48 / 98 and Contents 45 / 67 / 95 rounded once.
   Example: CA building 90%, Group II: 18 vs ISO 21.
2. **Below 80%.** The factor for 50% / 60% / 70% / None / Less Than 50% now comes from the state's in-force rules and
   tables, in the new `TBL - CoinsLT80` (building, contents and Group II factor per state and level, plus the variant).
   - CW: LessThan80 (1.5); Group II uses the flat factor (1.5).
   - FL: Group II 1.42, but 70% = 1.14 from its coinsurance table.
   - NY: building and all Group II use CoinsuranceModificationFactors (1.3 / 1.2 / 1.1 / 1.5 / 1.5); contents use
     LessThan80.
   - PR: 1.0.
   Contents Group I / Broad / Special priced **0** before (CA 70%: 0 vs ISO 535 / 241).
3. **Probes (Excel = ISO = engine unless noted):**
   - CA building 90%, contents 70%, contents 90%: all match.
   - NY 70%: matches.
   - FL 70% / 60% (location 1's building switched to CovType Building, credit and heating flags off): the coinsurance
     factors match ISO (1.14 / 1.42). Building Group II is still 6-7 low from gap F-2 below.
- **Found, not fixed (user's call), FL location 1 turned into an ordinary building (baseline building 1 is Legal
  Liability, which skips both steps):**
  - **F-1 heating plant:** Excel's multi-residential factor applies 0.75 for the heating plant even with the credit off
    (0.525 with it on). ISO's heat factor is 1.0 in both cases (0.70 with the credit).
  - **F-2 FL Group II deductible:** $2,500 gives Excel 0.95 vs ISO 0.951.
- **Payload gap:** the watchman and burglary-alarm credits are never sent, while the rater applies them. Any non-1.0
  credit would mismatch ISO.

## F-1 / F-2 / watchman-burglary -- DONE 2026-09-24 (`124 --fix MRC / FLDED / WBC`; `scenarios/fl_misc/`, `scenarios/coins/`)

- **F-1 multi-residential credit (`MRC`).** ISO: R3(heat x control) only when the location takes the credit AND the
  building class is 0311-0343; otherwise 1.0. The heat factor reads the building's `LocOfHeatingPlantIndicator`.
  - CS 51 multiplied the two for every building.
  - The payload never sent the field, so ISO used a heat factor of 1.0.
  - Now: CS 51 is gated and rounded. The payload sends the location's Schedule M, or "Not Applicable" when the location
    takes no credit.
  - Probes, FL building switched to CovType Building: credit + heating 0.525 = ISO; no credit 1.0 = ISO.
- **F-2 FL calendar-year deductibles (`FLDED`).** For FL residential classes (0074-0079, 0196-0198, 0311-0343; the
  building's class for contents), Group I / II / Broad / Special deductible factors come from
  `DeductibleFactorCalendarYear` (new `TBL - FLCalYearDed`). Wrapped CS 44, 89, 109, 123, 129 and 140.
  - Probes: FL coinsurance 70% / 60% now 15 / 15.
  - **Not done:** FL % wind/hail, EQ and sinkhole deductibles also use this table.
- **Watchman / burglary (`WBC`).** ISO applies both only when the contents have no theft exclusion. They come from the
  building's `CommercialPropertyBurglaryAndRobberyProtectiveSafeguards` record:
  - `BurgRobbery3ConvertedCode` Option75 / 85 / 95 must be sent; missing = 0.0.
  - `BurglaryAlarmCreditFactor` applies when the alarm type is set.
  - Rater Contents 92 / 93 are now gated. The payload sends the record from the building's contents and aborts if they
    disagree (ISO holds one set per building).
  - Probes, CA: 0.86 / 0.8 applied = ISO; with a theft exclusion both are 1.0 = ISO.
