# Gate — Subline 335, Owners & Contractors Protective / Principals Protective

**Build-order item 3** (`GL-RATING-ENGINE-BUILD-PLAN.md` §8). Presented against the eight-point
per-subline gate in §9.

**Status: PASSED, with one limitation stated up front — there is no oracle.** The corpus holds
**one** rated output (the Oklahoma golden case) and it carries no OCP coverage. Of 516 STC
submissions, **8 carry a real OCP exposure and none has an expected output.** So this gate rests on
derivation from ERC, confirmation against the filed manual at six points, and three corpus-wide
consistency tests — not on reproducing a published premium. §8 gives a fully worked example from a
real ISO submission, **labelled as derived and unvalidated**, and it becomes a regression fixture
the moment an oracle exists.

Shared machinery is cited to [`GATE-334`](GATE-334-PREMISES-OPERATIONS.md) and
[`GATE-336`](GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md) rather than re-derived.

---

## 0. The finding: the 2027 program deleted half of this coverage

335 is the sharpest edition split found so far — larger than 334's, and structural rather than
arithmetic. Comparing `GL_CW_20230501_V01` / `GL_CW_20231201_V03` against `GL_CW_20270401_V01`:

| | CW 2023 | CW 2027 |
|---|---|---|
| Rating steps | **21** (11 + 10) | **12** (6 + 6) |
| Published loss-cost path | `SetLossCost`, `…OverOneMillion`, `…OverOneHundred` | **all three rules deleted** |
| Marginal tiers | **two breakpoints** — `$1,000,000` and `100 units` | **one** — `$1,000,000` |
| Workers Compensation input | `SetELP` special-cases class `15191`: `ELP = PrincipalsProtvLiabFactor × WorkersCompensationRate` | **removed — `SetELP` no longer references it** |
| Minimum premium | `SetMinimumPremium` + `SetMinPremium` | **both deleted** |
| Class codes hardcoded in `SetPremium` | `27111`, `27112` | **none** |

And the data moved with the rules — **on a single future date.**

> ### ⚠ Correction, same day — this section was first filed with a defective measurement
>
> The figures below originally read *"published in 8 jurisdictions, absent in 43"* as a statement
> about **now**. They were taken over the **latest** package per jurisdiction, and the corpus holds
> **82 state packages effective after today**. That is the end state, not the present one — the
> exact error N4 exists to prevent, made while documenting N4.
>
> Re-measured as-of a date (`scripts/erc/31_migration_asof.py`):
>
> | As of | Publishing OCP loss costs | Absent |
> |---|---|---|
> | **2026-08-11 (today)** | **51** | **0** |
> | 2027-04-01 | 8 | 43 |
> | latest filed | 8 | 43 |
>
> **Today every jurisdiction publishes them. The withdrawal is entirely in the future**, and it is
> a **cliff**: 43 jurisdictions lose the table on one day. The gate's conclusion — *both paths are
> needed by effective date, not by jurisdiction* — is unchanged and sharper, because today the
> loss-cost path is the one that is always needed. Full account in
> [`RECONCILIATION.md`](RECONCILIATION.md) §1.

Measured across the **end state** (all filings in force), which is what the rest of this gate
describes:

- **OCP loss costs are published in 8 jurisdictions** — CA, FL, GA, MA, NJ, NV, NY, WA — and the
  table is **absent entirely in the other 43**.
- **All 51 publish them today**, and all 51 published them in every earlier edition.
- **The 43 that withdraw them are exactly the 43 whose `2027-04-01` package is in the corpus. Zero
  exceptions in either direction.**

The class list changed with it:

| | Classes |
|---|---|
| Retired by 2027 | `15191` · `15192` · `27111` · `27112` |
| Introduced by 2027 | `27113` |
| Unchanged | `16291` · `16292` · `17982` · `91161` · `91162` · `91181` · `93040` · `93161` · `93163` |

The two retired `271xx` classes are **precisely the two hardcoded in the pre-2027 `SetPremium`** as
using the 100-unit basis. The 2027 program replaces both with a single `27113` and drops the
special basis with them.

**What this means for the build.** The build plan's line — *"published loss costs in 15
jurisdictions, withdrawn in 36 — both paths needed"* — is right that both paths are needed and wrong
about the split and its cause. It is not a division between states at all: it is **one dated program
change**, and **as of today it has not happened yet**. So:

- Both paths are needed **because of the effective date**, not because of the jurisdiction. **Every**
  jurisdiction needs the loss-cost path for a risk incepting today; 43 of them stop needing it on
  2027-04-01. Same state, two answers, decided by the date.
- **N4 is not a tail case for 335, it is the whole coverage.** Two different algorithms, two
  different class lists, two different premium functions, selected by the resolved parent.
- This is the third gate in a row where **resolving the declared parent first** (habit 1) changed
  the answer. Here it changes which of two coverages you are building.

---

## 1. The algorithm

Class-level coverage, no territory dimension, **no deductibles** (see §2), no size-of-risk, and —
unlike 334 and 336 — **no `PackageModFactor`**.

### CW 2023 and earlier — 21 steps

`ErcSetRatesAndFactors` (11): `SetLossCost` · `SetLossCostOverOneMillion` ·
`SetLossCostOverOneHundred` · `SetPrincipalsProtvLiabFactor` · `SetELPOverride` ·
`SetELPOverOneMillionOverride` · `SetLCM` · `SetELP` · `SetELPOverOneHundred` ·
`SetELPOverOneMillion` · `SetILF`

`ErcRate` (10): `SetBaseRate` · `SetBaseRateOverOneMillion` · `SetBaseRateOverOneHundred` ·
`SetFinalRate` · `SetFinalRateOverOneMillion` · `SetFinalRateOverOneHundred` ·
`SetMinimumPremium` · `SetMinPremium` · `SetPremium` · `SetPremiumIndicator`

### The arithmetic — and it is not `rate × exposure`

Every prior subline computes one rate and multiplies. **OCP is a piecewise-linear marginal
function with a class-dependent breakpoint and a class-dependent divisor:**

```
BaseRate      = round( LossCost × LCM , 3)     when LossCost ≠ 0
              = round( ELP      × LCM , 3)     when LossCost = 0
FinalRate     = round( BaseRate × ILF × ExperienceRatingModificationFactor
                                × ExpenseModification × ModToUse , 3)
                (and the same for the OverOneMillion / OverOneHundred bands, each from its
                 own loss-cost / ELP table)

                                     ┌ class ∈ {27111, 27112}      other classes
        breakpoint                   │ 100 units                   $1,000,000
        divisor                      │ none                        ÷ 1000

Premium = round( FinalRate                 × min(exposure, breakpoint) / divisor
               + FinalRateOverBreakpoint   × max(0, exposure − breakpoint) / divisor , 0)

MinPremium = round( MinimumPremium × ILF , 0)      # no AdditionalInterestFactor, unlike 336
```

Three consequences an implementation must not miss:

1. **The premium function is piecewise.** A single `rate × exposure` kernel cannot express it. The
   engine's premium step has to be a per-subline strategy, not a shared helper.
2. **The breakpoint and the divisor are selected by a hardcoded class list**, and that list is
   edition-scoped (`27111`/`27112` pre-2027, empty after). A class list read from a table would be
   wrong; it is in the rules.
3. **The second tier reads its own rate tables** — `OwnersContractorsLossCostOverOneMillion`,
   `OwnersContractorsELPOverOneMillion`, and the `OverOneHundred` pair. Six rate sources for one
   coverage.

### The third rating path — Workers Compensation, class 15191

`SetELP` branches three ways on class code:

```
class = ""            → ELP = 0.0
class = 15191         → ELP = PrincipalsProtvLiabFactor × WorkersCompensationRate
otherwise             → ELP = LookupOwnersContractorsELP(state, class)
```

`PrincipalsProtvLiabFactor` is a countrywide single-cell table: `"CW","Y",0.75`. The
`WorkersCompensationRate` is **a declared submission input** — `MasterGLCW.DataDef.xsd` defines it
as `xs:decimal`, 4 fraction digits — and a real STC submission supplies it (`1000.0`, §8).

**So the Workers Compensation "external dependency" is neither missing nor external.** The 75% is in
ERC; the WC rate is an input field, exactly like exposure. This resolves the fourth entry in
`README.md`'s *"What is not here"* the same way E8 resolved geocoding: **a submission requirement,
not a corpus gap.** And under CW 2027 it does not arise at all — class 15191 is retired and `SetELP`
no longer references the field.

### CW 2027 — 12 steps

`SetELPOverride` · `SetELPOverOneMillionOverride` · `SetLCM` · `SetELP` · `SetELPOverOneMillion` ·
`SetILF`, then `SetBaseRate` · `SetBaseRateOverOneMillion` · `SetFinalRate` ·
`SetFinalRateOverOneMillion` · `SetPremium` · `SetPremiumIndicator`.

Purely ELP-driven, one breakpoint, no minimum premium, no external input.

**A dead lookup survives the change:** `LookupPrincipalsProtvLiabFactor` is still present in the CW
2027 rule set but is called by nothing, because `SetPrincipalsProtvLiabFactor` was deleted. Recorded,
not implemented — the same treatment `AdditionalInterestFactor` got in gate 334.

---

## 2. Confirmations

The manual is unusually informative on this coverage, and every check agreed.

| Claim | Manual says | Citation | Verdict |
|---|---|---|---|
| Subline code is 335, and OCP and Principals Protective are one rule | *"RULE 46. OWNERS AND CONTRACTORS PROTECTIVE LIABILITY INSURANCE AND PRINCIPALS PROTECTIVE LIABILITY INSURANCE (Subline Code 335)"* | `GL-MU-2027-RU-001-C` p.103 | **Confirms** the subline code and that one ERC rule set covers both |
| **Deductibles do not apply** | *"B. Exceptions To Section I – General Rules … 2. Rule 15. Deductibles does not apply."* | `GL-MU-2027-RU-001-C` p.104 | **Confirms** ERC exactly — the OCP rule set has **no deductible rules at all**, where 334 and 336 each have five |
| Rule 5 Premium Computation does not apply | *"1. Rule 5. Premium Computation does not apply."* | same page | **Confirms** that OCP has its own premium function rather than the standard one — the piecewise structure of §1 |
| Class 15191 is priced off Workers Compensation at **75%** | *"15191 Percentage of otherwise applicable Workers Compensation loss costs: **75%**"* | `GL-AK-2020-LC-001-C` p.9, Table 5.C. OCP & PP ELPs | **Confirms `PrincipalsProtvLiabFactor = 0.75`** — ERC's countrywide cell, from an independent source |
| The published ELP values | `15192` $0.95 · `91181` $0.54 · `93161` $0.68 · `93163` $0.48 | same table | **Confirms all four**, matching `OwnersContractorsELP` in NJ and AR to the cent |
| **`RTC` marks classes 17982 and 93040** | those two rows print `RTC`, not a dollar amount | same table | **Confirms that ERC's selector value `Company` means refer-to-company** — see §7. The single most useful confirmation in this gate |

**No disagreement was found between the two sources on the 335 algorithm.**

Note the ELP Supplement cited is an **Alaska** notice, and its values match **New Jersey's and
Arkansas's** ERC tables exactly. The OCP ELP table is countrywide in substance even though ERC
stores it per state — consistent with the `FirstNonNull(state, "CW")` mechanism (N16), and a useful
sanity check on both sources at once.

---

## 3. Escalations

| # | Question | Engine behaviour meanwhile |
|---|---|---|
| **E1** | Rounding tie-break | 🟠 **now demonstrably live.** §8 finds the project's **first real midpoint**: AR class 15192, `BaseRate 0.95 × ILF 1.75 = 1.6625`, an exact 3dp tie. `HALF_UP → 1.663`, `HALF_EVEN → 1.662`. The premium happens to be `249` either way at this exposure, so it still does not *settle* E1 — but E1 is no longer theoretical, and a different exposure on the same rate would separate them. **Raises the priority of the RAaS question** |
| **E11** | `AdditionalInterestFactor` | unchanged — 335 does not read it either (336 does) |
| **E14** *(new)* | `LookupPrincipalsProtvLiabFactor` survives in CW 2027 with no caller, after `SetPrincipalsProtvLiabFactor` was deleted. Vestigial, or a deletion defect? | Not implemented. Zero premium effect. Cheap to ask alongside E11 — **both are the same shape**: a computed-or-callable artifact with no consumer, which may indicate the published rule set lags the program change |

---

## 4. Inputs consumed, and behaviour when absent

| Input | ERC on absence | **Engine** |
|---|---|---|
| `OwnersContractorsClassCode` | `SetPremium`'s outer test fails → **`Premium = 0.0`** | `REFER` |
| `OwnersContractorsClassDescription` | `SetELP` and `SetILF` both return `0.0` → base rate and ILF both zero | `REFER` — note ERC gates the **rate** on the *description*, not the code |
| `OwnersContractorsExposure` | `0` → premium `0`; **no `$1` floor in any edition** | `REFER` unless `MiscIfAnyBasis = "Yes"` |
| `OwnersContractorsEachOccurrenceLimit`, `OwnersContractorsAggregateLimit` | either empty → `ILF = 0.0` → premium `0` | `REFER` |
| **`WorkersCompensationRate`** | absent on a class-`15191` risk → `ELP = 0.0` → **`Premium = 0`** | `REFER`. **Required whenever class 15191 is present**, pre-2027 only |
| `Subline` ≠ `"Owners and Contractors"` | `MinPremium = 0.0` — the minimum is silently not applied | validate against the domain |

**`SetELP` and `SetILF` gate on `OwnersContractorsClassDescription` while `SetLossCost` and
`SetPremium` gate on `OwnersContractorsClassCode`.** A submission carrying the code but not the
description gets a loss cost and no ILF — `FinalRate = BaseRate × 0` — and a **zero premium** rather
than an error. The engine requires both, or refers.

**The limit vocabulary differs from 334/336.** OCP limits are `"1,000,000"` / `"2,000,000"`;
Prem/Ops and Prod/CompOps use `"1,000,000 CSL"` / `"2,000,000 CSL"`. Same numbers, different
strings, different tables. A shared limit-normalisation helper across sublines will miss every OCP
ILF lookup and return `0.0`.

---

## 5. Lookups and their layer

| Table | Countrywide | State | Layer |
|---|---|---|---|
| `OwnersContractorsLossCost` (+ `…OverOneMillion`, `…OverOneHundred`) | **0 rows** (header only) | 11 rows in 8 jurisdictions; **absent in 43** | **state only** |
| `OwnersContractorsELP` (+ the two band tables) | **0 rows** | populated in all 51 | **state only** |
| `OwnersContractorsELPText` | **0 rows** | **all 51, 433 rows** | **state only** |
| `ILFOwnersContractors` | **0 rows** | populated | **state only** |
| `PrincipalsProtvLiabFactor` | **1 row — `"CW","Y",0.75`** | — | **countrywide only** |
| `PremOpsMinPremium` *(OCP reuses it)* | 3 rows | — | **countrywide only** |

Five more header-only countrywide tables in a live rating path (N7). **OCP's minimum premium reuses
the Premises/Operations table** — `LookupPremOpsMinPremium`, not an OCP-specific one. A per-subline
table-name convention would look for a table that does not exist.

**Keying differs from every prior subline:** the loss cost and ELP lookups are keyed on
**(state, class)** with **no territory**, and the ILF on **(state, occurrence limit, aggregate
limit)** with **no increased-limits table assignment**. OCP has neither a territory dimension nor a
table-assignment dimension.

---

## 6. State deviations

`scripts/erc/29_census_336.py --rules GeneralLiabilityClassificationOwnersContractorsCoverageRules`

**49 of 51 jurisdictions are pure countrywide**, on both the latest edition and across all 562
packages. The complete list of overrides:

| Rule | Jurisdictions | Effect |
|---|---|---|
| `SetILF` | **NY** | own increased-limits treatment |
| `SetMoldStatCode` | AK, NY | statistical coding only |

**OCP is the most uniform coverage examined**: 334 has 19 jurisdictions overriding, 336 has 22, OCP
has 2 — and only one of those touches premium. **All of OCP's variation lives in the data**, not in
the rules: which states publish loss costs (§0), which classes are refer-to-company (§7), and the
per-state ELP and ILF values.

That is a useful shape to know before building: for 335 the state layer can be treated as pure data,
with a single algorithm plus one NY exception.

---

## 7. Refer-to-company triggers

### `Company` in the selector means Refer To Company

The manual's ELP Supplement prints `RTC` for classes `17982` and `93040`. ERC marks exactly those
classes `Company` in `OwnersContractorsELPText` — **and carries `0` in the ELP table for every one
of them.**

Tested across the latest edition of all 51 jurisdictions — **433 (state, class) rows, and every
jurisdiction has the selector table:**

| Test | Result |
|---|---|
| selector `Rate/Loss Cost Applies` ⟺ a non-zero published loss cost | **433 / 433 agree, 0 disagree** |
| selector `Company` ⟺ `ELP == 0` | **147 / 147 agree, 0 disagree** |
| selector `Industry` ⟺ `ELP ≠ 0` | 246 / 254 agree — **all 8 exceptions are class `15191`** |

The 8 exceptions are not exceptions. Class `15191` is `Industry` with a table ELP of `0` **because
its ELP is not in the table** — it is computed from the WC rate input (§1). The rules discriminate it
explicitly by class code, and it occurs in exactly the 8 jurisdictions that still carry the class.

**So on this subline the selector explains every single zero**, across three different reasons for a
zero. This is the strongest evidence yet for **N17**, and it comes from the coverage where it matters
most: with the loss-cost table absent in 43 jurisdictions, almost every OCP risk takes the ELP path,
where an unguarded `0` means a **free policy**.

### The zero taxonomy is now five

| Meaning of `0` | Example | Discriminator |
|---|---|---|
| a genuine factor | `DedFactorPremOpsCSL` "No Deductible" | the value is correct as read |
| an **unpublished** factor | the 15 "Per Claim" deductible factors | a `DoMessage*` validation rule (N15) |
| an **unguarded refer** | drone `>55 lb` band | **none in ERC** — the manual |
| a **path switch to a table** | `ProdsCompldOpsLossCost = 0` → the ELP | the `*ELPText` selector (N17) |
| a **path switch to an input** *(new)* | `OwnersContractorsELP = 0` for class `15191` → `0.75 × WC rate` | a hardcoded class-code branch in `SetELP` |

Four of five now have an in-corpus discriminator. Only the drone case still requires the manual.

### The full trigger list

1. **`ELPText = "Company"` — 147 (state, class) pairs across all 51 jurisdictions.** Most common:
   `93040` (51 jurisdictions), `93161` (43), `27113` (43), `17982` (8), `91161` (1), `91162` (1).
   Class `93040` is refer-to-company **everywhere, in every edition**. `REFER` on the selector,
   never on the `0`.
2. **Class `15191` with no `WorkersCompensationRate`** — §4. Pre-2027 only.
3. **`ILF = 0.0`** from an empty or off-domain limit pair — `FinalRate` becomes `0`.
4. **Class code present without class description** — §4, yields a zero premium silently.
5. **A 2027-edition risk needing a published loss cost** — there are none; every 2027 OCP risk is
   ELP-driven or referred.

---

## 8. Test result — no oracle, and a worked example

**There is no expected output for OCP anywhere in the corpus.** One rated output exists (Oklahoma,
gate 334/336) and it carries no OCP coverage. Of 516 STC submissions, **8 carry an
`OwnersContractorsExposure`** and none has a paired output. Stated plainly rather than worked
around: **this gate is not validated against ISO arithmetic.**

What follows is derived from the rules and tables, on a **real ISO submission**
(`AR/GL AR 20230501 V01/STC/STC_GL000074745.json`), and is **a prediction, not a confirmation.**

Parent resolved from the XSD: **`GL_CW_20230501_V01`** — a third distinct countrywide edition, whose
OCP rule set was verified step-for-step identical to `GL_CW_20231201_V03` before being relied on
(habit 1).

Risk: Arkansas, effective 2023-05-01, `Owners and Contractors`, occurrence form, limits
`1,000,000 / 2,000,000`, `PackageModFactor 1.0`, two classifications, `WorkersCompensationRate
1000.0`.

**Table cells consumed** — `ILFOwnersContractors["AR","1,000,000","2,000,000"] = 1.75` ·
`OwnersContractorsLossCost["AR","15191"] = 0` and `["AR","15192"] = 0` (no published loss costs) ·
`OwnersContractorsELPText` both `Industry` · `OwnersContractorsELP["AR","15192"] = 0.95`,
`["AR","15191"] = 0` (the input-derived class) · `PrincipalsProtvLiabFactor["CW","Y"] = 0.75`.

| Step | Class `15191` — Principals Protective, Cov A | Class `15192` — Cov B |
|---|---|---|
| basis | selector `Industry`; class-`15191` branch → **input-derived** | selector `Industry` → table ELP |
| `ELP` | `0.75 × 1000.0` = **`750.000`** | **`0.95`** |
| `BaseRate` | `round(750.0 × 1.0, 3)` = `750.000` | `round(0.95 × 1.0, 3)` = `0.950` |
| `FinalRate` | `round(750.0 × 1.75, 3)` = `1312.500` | `round(1.6625, 3)` = **`1.663`** ⚠ |
| exposure | `10,000` (Total Cost) | `150,000` (Total Cost) |
| tier | ≤ $1,000,000 → single tier, ÷1000 | ≤ $1,000,000 → single tier, ÷1000 |
| **`Premium`** | `round(1312.5 × 10, 0)` = **`13,125`** | `round(1.663 × 150, 0)` = **`249`** |

⚠ **`0.95 × 1.75 = 1.6625` is an exact 3dp midpoint — the first genuine rounding tie found in this
project.** `HALF_UP` gives `1.663`; `HALF_EVEN` gives `1.662`. At this exposure both yield `249`, so
the case still does not settle E1 — but it demonstrates that midpoints **do** occur on real
submissions, which the golden case had suggested they might not. See §3.

**Neither premium is validated.** Both become assertions the moment an OCP oracle exists; the 8 OCP
submissions are recorded as the seed set for that fixture.

---

## 9. Corrections filed

| Document | Was | Now |
|---|---|---|
| §8 build order, item 3 | *"Published loss costs in 15 jurisdictions, withdrawn in 36 — both paths needed"* | **Not a jurisdiction split and not in flight.** As of today **51 publish, 0 withdrawn**; on `2027-04-01` **43 withdraw simultaneously**. One dated program change. Both paths needed **by effective date** |
| §4, N4 | as-of, never latest | **335 is the strongest case.** Two different algorithms (21 steps vs 12), two class lists, two premium functions, one selected by the resolved parent |
| §4, N13 | four meanings of `0` | **five.** New: a `0` that switches to an **input-derived** computation (`OwnersContractorsELP` for class `15191`). Four of five now have an in-corpus discriminator |
| §4, N17 | 620,856 agreements on Prem/Ops | **Corroborated a third time, on the hardest subline.** OCP: 433/433 and 147/147 exact; the 8 apparent exceptions are the input-derived class. **`Company` = the manual's `RTC`** — confirmed against `GL-AK-2020-LC-001-C` p.9 |
| §6, premium chain | `Premium = round(FinalRate × Exposure[/1000] [+ MedPayCharge], 0)` | **Not general.** OCP is **piecewise-linear with a class-dependent breakpoint and divisor**, reading six rate tables. The premium step is a per-subline strategy, not a shared helper |
| `README.md`, *What is not here* | *"Workers Compensation loss costs — one OCP class is priced as 75% of the applicable WC loss cost"*, listed as a missing input | **Not a gap.** The 75% is in ERC (`PrincipalsProtvLiabFactor`, countrywide); the WC rate is a **declared submission field** and a real STC submission supplies it. Resolved like E8. **Retired entirely by the 2027 program** |
| §7, E1 | *"golden case does not hit a midpoint"* | Still true — but **a real submission does** (`1.6625`). E1 is live, not theoretical |
| §7, new E14 | — | `LookupPrincipalsProtvLiabFactor` survives in CW 2027 with no caller |
| §5, architecture | one limit vocabulary | **OCP limits are `"1,000,000"`; 334/336 use `"1,000,000 CSL"`.** A shared normaliser breaks every OCP ILF lookup |
| §11, testing | golden case covers the chain | **335 has no oracle.** 8 OCP submissions exist without outputs; recorded as the seed fixture set |

---

## 10. Verdict

**Gate passed**, with the oracle gap stated rather than papered over. The derivation is complete,
the manual agreed at all six checks, and three corpus-wide tests came back exact.

**The habits held, and one earned its keep three times running:** resolving the declared parent
first (habit 1) has now changed the answer in every gate — an arithmetic split in 334, a
no-split confirmation in 336, and here **two different coverages**.

**A seventh habit, from this gate — and it caught me the same day I wrote it: when a document
states a jurisdiction split, test whether it is really an *edition* split, and then measure it
as-of a date.** "15 published / 36 withdrawn" reads as geography; it is a calendar. My own
replacement figure, 8/43, read as *now*; it is the end state. Applied properly to README finding
#4's class-basis split, the answer is the same: **51/0 today, 8/43 from 2027-04-01** — one cliff,
not a migration in progress. See [`RECONCILIATION.md`](RECONCILIATION.md) §1.

**Next:** build-order item 4, Liquor Liability (332) — *"no published base rate anywhere;
ELP-driven or refer"*. On the evidence of this gate that description deserves the same test: the
`LiquorELPText` selector has only **two** values corpus-wide (`Industry`, `Company`) and no
`Rate/Loss Cost Applies` at all, so N17 predicts liquor is **entirely** ELP-or-refer — the first
subline where the loss-cost path should not exist even in principle. That prediction is worth
recording now and checking first.
