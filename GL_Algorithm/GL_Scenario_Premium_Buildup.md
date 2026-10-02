# A worked scenario — how six coverages become one policy premium

**The risk.** One location, one classification (Mercantile), written on the
*Premises/Operations and Products/Completed Operations* subline, with:

- **Premises/Operations** coverage
- **Products/Completed Operations** coverage
- **Liquor Liability**
- **Medical Payments at $10,000**
- **Terrorism (TRIA) accepted**
- **Minimum premiums** in play

**Source:** `GL CW 20270401 V01` (V02 identical for everything here). **Companions:**
`GL_Premium_Map.md` (the whole line), `GL_PremOps_Prods_Premium_Trace.md` (the two core
coverages in detail), `GL_Premium_Tree.html` (navigable).

**Written:** 2026-09-17.

**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — the scenario was built
and rated offline (strict-erc): Oklahoma, class 10026 *Antique Stores* (Mercantile), $1,000,000
gross sales on both coverages, 1,000,000 CSL, Med Pay $10,000, `TerrorismCoverage = Yes`, at
**2027-04-01** (`GL_OK_20270401_V04` over `GL_CW_20270401_V02`) and at **2026-10-02**
(`GL_OK_20261001_V01` over `GL_CW_20261001_V01`). The run **corrected four claims** this page
used to make — Liquor on the same risk, the terrorism formula, a declined-terrorism zero, and the
caller-supplied minimum top-up — each marked *Corrected 2026-10-02* below. All 16
`tests/verify_*` suites pass.

> **Edition scope.** The mechanics below are the **2027-04-01 edition**. A policy effective
> before that date (today: CW 20260101 V01 for 46 jurisdictions, 20261001 V01 for OK, 20231201
> V03 for NJ/TX/VT, 20231201 V02 for CA — and GA, NJ, NY, WA, CA even after the cliff) prices
> Med Pay and minimum premium differently; §7 gives the same scenario rated on the in-force
> edition.

---

## 0. What the engine produced

| | 2027-04-01 | with Med Pay at the included $5,000 |
|---|---|---|
| Prem/Ops `Premium` | **827** | 824 |
| Products `Premium` | **21** | 21 |
| Terrorism — Prem/Ops | **3** | 3 |
| Terrorism — Products | **1** ($1 floor) | 1 |
| Liquor | **0** — see §2 | 0 |
| Minimum-premium top-ups | **0** — see §4 | 0 |
| **Policy total** | **852** | 849 |

---

## 1. First correction: that is five premium-bearing things, not six

**Medical Payments does not produce a premium.** There is a `GeneralLiabilityMedPayCoverage`
record, and it does sit in the roll-up — but its rule file contains only `InitializeRuleSet`,
`CalculateTotalPremium` and `ErcProcess`. **No `SetPremium`, no rating logic of any kind.** The
one thing that ever writes its `Premium` is a line in `ErcProcess` that forces it to `0.0` when
the coverage is off.

Medical Payments is priced as a **factor inside the Premises/Operations rate**:

```
if MedPayCoverage/Limit = "5,000":            MedicalPaymentsFactor = 1.0     (the included limit)
otherwise:                                     MedicalPaymentsFactor = LookupIncreasedMedPayLimitFactor(
                                                    State|CW, ClassificationType, MedPayLimit )
```

and then, in `SetFinalILF` on the Prem/Ops coverage:

```
FinalILF = round( (CSLILF + MedicalPaymentsFactor − 1) − FinalDeductibleFactor , 3 )
```

(skipped — plain `CSLILF − FinalDeductibleFactor` — when a Coverage C Medical Payments exclusion
is attached at the classification or location).

At **$10,000, Mercantile**, the countrywide factor is **1.007** — so Med Pay adds **0.007 to
the ILF**. *Engine:* `CSLILF` 2.01 → `FinalILF` **2.017**, `FinalRate` 0.410 × 2.017 = 0.827,
Prem/Ops premium **827** against **824** at $5,000 — **$3**, about 0.4%. Contracting or
Servicing pays 1.011 for the same limit.

*Corrected 2026-10-02 — the full table (CW 20270401 V01 and V02, `IncreasedMedPayLimitFactor`,
20 rows; the earlier version showed a dash for Contracting at $20,000 and stopped there):*

| Increased Med Pay limit | Mercantile, Miscellaneous, Manufacturing or Processing, Buildings or Premises | Contracting or Servicing |
|---|---|---|
| 10,000 | 1.007 | 1.011 |
| 15,000 | 1.011 | 1.017 |
| 20,000 | 1.014 | 1.022 |
| 25,000 | 1.016 | 1.026 |

**Consequences worth knowing.** Med Pay never appears as a line item. It touches
**Premises/Operations only** — not Products, not Liquor (engine: Products `FinalILF` stays
1.760). And because it lands inside `FinalILF`, it is inside the terrorism base too (§3).

---

## 2. The premiums, and where each is computed

| # | Coverage | DataDef group | Depth | Computed by |
|---|---|---|---|---|
| 1 | Premises/Operations | `GeneralLiabilityClassificationPremOpsCoverage` | 3 | `SetPremium` |
| 2 | Products/Completed Ops | `GeneralLiabilityClassificationProdsCompldOpsCoverage` | 3 | `SetPremium` |
| 3 | Liquor Liability | `GeneralLiabilityClassificationLiquorCoverage` | 3 | `SetPremium` — **on a separate risk**, see below |
| 4 | Terrorism — Prem/Ops | `GeneralLiabilityTerrorismPremOpsCoverage` | **4** | `SetPremium` |
| 5 | Terrorism — Prods/CompldOps | `GeneralLiabilityTerrorismProdsCompldOpsCoverage` | **4** | `SetPremium` |
| (5b) | Terrorism — all other sublines | `GeneralLiabilityTerrorismAllOtherSublineCoverage` | **4** | `SetPremium` — this is where **Liquor's** terrorism charge lands |

> **Corrected 2026-10-02 — Liquor cannot sit on this risk.** Every coverage on a classification
> is switched on by the *policy's* `Subline`.
> `GeneralLiabilityClassificationLiquorCoverage.SetCoverageOnPolicyIndicator` is `1` only when
> `Subline = "Liquor"`; Prem/Ops is `1` only for *Premises/Operations and Products/Completed
> Operations*. One `GeneralLiability` risk has one subline, so a liquor record added to this risk
> is gated off: rated by the engine, it contributes **0** and the total stays 852. **Liquor is
> written as a second `GeneralLiability` risk** in the same submission (`Subline = "Liquor"`, its
> own liquor class, exposure and `LiquorCoverageForm`); the kernel adds the risks' totals (engine:
> a two-risk submission rates to exactly the sum of its risks). The policy premium for this
> scenario is therefore *this risk's total* **plus** *the liquor risk's total*.

Coverages 1–3 are siblings under their classification. The terrorism coverages sit one level
deeper, under a `GeneralLiabilityTerrorism` record that is itself a child of the classification.

### 1–3 share one shape

```
BaseRate  = round( LossCost × LCM , 3 )        Prem/Ops, Products; ELP × LCM when the loss cost is 0
          = round( ELP × LCM , 3 )             Liquor — always the ELP path (LiquorLossCost is header-only in CW)
FinalRate = round( BaseRate × FinalILF × SizeOfRisk × PackageMod
                     × ExperienceMod × ExpenseMod × ModToUse , 3 )
Premium   = round( FinalRate × Exposure / 1000 , 0 )
```

Only the field names differ — `PremOpsCovExposure`, `ProdsCompldOpsCovExposure`,
`LiquorExposure`. Size-of-risk applies only when `SizeOfRiskRatingApplies = Yes`; Liquor has no
size-of-risk term, and divides by 1,000 only for its gross-sales bases. *Engine:* Prem/Ops 0.41 →
0.410 → 0.827 → **827**; Products 0.012 → 0.012 → 0.021 → **21**.

> **The $1 floor.** If the arithmetic gives 0 while exposure is above 0, `Premium` is forced to
> `1.0`. Zero is reserved for "not covered". New in the 2027-04-01 edition.

---

## 3. Terrorism is a percentage of the other premiums

This is the part that makes the scenario order-dependent.

`SetClassCoveragePremium` on the terrorism coverage **sums the premiums of the underlying
coverages for that subline** — Prem/Ops, Loss of Electronic Data, Cyber Incident Liability and
the rest — and `SetPremium` then picks **one of three formulas**:

*Corrected 2026-10-02 — the earlier single formula multiplied every factor together; the rule
does not:*

```
TerrorismCoverage = "Yes":
    Premium = round( ClassCoveragePremium × CertifiedActsOfTerrorismExposureClassFactor , 0 )
an NBCR exclusion endorsement attached:
    Premium = round( ClassCoveragePremium × ExposureClassFactor × NuclBioChemRadioFactor , 0 )
a terrorism aggregate-cap / sublimit endorsement attached (e.g. CG 21 80):
    Premium = round( round( ClassCoveragePremium × ExposureClassFactor , 0 )
                     × round( TerrorismILF ÷ Prem/Ops FinalILF , 3 ) , 0 )
otherwise 0;  then the $1 floor if that is 0 while ClassCoveragePremium > 0
```

*Engine:* Prem/Ops 827 × 0.004 = 3.308 → **3**; Products 21 × 0.004 = 0.084 → 0 → **1** (floor).
`TerrorismILF` is written `1.0` and the NBCR factor 0.58 is looked up, but neither is used on the
accepted branch.

**So terrorism cannot be computed until coverages 1–3 are final.** It is a charge *on* the
premium, not a parallel one. Three consequences:

1. **The Med Pay uplift is inside the terrorism base.** A higher Med Pay limit raises Prem/Ops,
   which raises `ClassCoveragePremium`, which can raise the terrorism charge (here 827 vs 824
   both round to 3). Under a cap endorsement the effect partly cancels, because the Prem/Ops
   `FinalILF` is the divisor.
2. **Liquor's terrorism goes to a different record** — `…TerrorismAllOtherSublineCoverage` on
   the liquor risk, not the Prem/Ops one.
3. *Corrected 2026-10-02:* **declining `TerrorismCoverage` does not by itself zero the charge.**
   The NBCR and cap branches do not test `TerrorismCoverage`. Oklahoma's engine base submission
   declines terrorism but carries a CG 21 80 cap at $100,000, and the engine — like ISO's own
   Oklahoma output — prices terrorism at **18** (2 + 16) on it. Accepting without attaching a
   Certified Acts form also raises ISO's message *"A Certified Acts of Terrorism Form must be
   attached to the policy when coverage is accepted"* — the premium is still produced.

---

## 4. Minimum premium — switched off in this edition

Each of the three coverages owns a minimum-premium lookup — `LookupPremOpsMinPremium`,
`LookupProdsCompldOpsMinPremium`, `LookupLiquorMinPremium`, plus Prem/Ops's
`LookupSpecialCombinedMinPremium`. And there are three dedicated records at **policy level**:

- `GeneralLiabilityPremOpsPremiumToReachMinCoverage`
- `GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverage`
- `GeneralLiabilityLiquorPremiumToReachMinCoverage`

Each is a leaf at depth 1 that is summed into the account total. **But nothing computes what goes
in them.** Their rule files hold only `InitializeRuleSet`, `CalculateTotalPremium`,
`SetCoverageOnPolicyIndicator` and `ErcProcess` — no `SetPremium` — and the related datadefs
`PremiumToReachMin` and `TotPremiumPriorToMin` are, corpus-wide, **written 0 times and read 0
times**.

> *Corrected 2026-10-02 — **and you cannot fill them either.*** This page used to say the caller
> could put a shortfall in these records and the roll-up would add it. It will not:
> `SetCoverageOnPolicyIndicator` on all three writes `0` **unconditionally**, so `ErcProcess`
> forces `Premium = 0` whatever was sent. Engine test: `Premium = 100` supplied on the Prem/Ops
> record, total unchanged at 852. **In the 2027-04-01 edition a minimum premium has to be applied
> entirely outside ISO's rating** — compare and top up after the engine returns.
> The coverage-level lookups are not even invoked by the engine's 2027 runs.

---

## 5. How it all comes together

```
                                   policy premium  =  risk 1 total  +  risk 2 total
                                                         ▲                  ▲
                                   GeneralLiability (Prem/Ops & Products)   GeneralLiability (Liquor)
                                   .ErcCalculatedTotalPremium = 852         .ErcCalculatedTotalPremium
                                                         ▲                  (Liquor Premium + its
        ┌────────────────────────────────────────────────┼──────────┐        All-Other terrorism)
        │                                                │          │
  PremOpsPremiumToReachMin    0      GeneralLiabilityLocation       (400+ other policy-level
  ProdsCompldOpsPremiumToReachMin 0  .ErcCalculatedTotalPremium 852  endorsements, 0 here)
  — depth 1, forced to 0 —                    ▲  depth 1
                                   GeneralLiabilityClassification
                                      .ErcCalculatedTotalPremium 852
                                               ▲  depth 2
        ┌──────────────────┬───────────────────┴──────────────┐
        │                  │                                  │
   Prem/Ops 827      Products 21                 GeneralLiabilityTerrorism 4
   depth 3           depth 3                                  ▲  depth 3
   ▲                                               ┌──────────┴──────────┐
   │                                          Terr PremOps 3       Terr Prods 1
   └── Med Pay $10,000 enters here,           depth 4              depth 4 ($1 floor)
       as +0.007 on FinalILF                  (each = ClassCoveragePremium × 0.004)
```

**Order of computation:**

1. Rate and price Prem/Ops and Products — Med Pay's 1.007 is inside Prem/Ops's ILF.
2. Sum those into `ClassCoveragePremium` per subline; compute the terrorism charges.
3. Roll the terrorism record up into the classification alongside 1–2.
4. Classification → location → risk.
5. Rate the Liquor risk the same way; the submission total is the sum of the risks.
6. **Separately, outside ISO's rating**, compare each subline's premium against its minimum —
   the `…PremiumToReachMinCoverage` records cannot carry the top-up in this edition.

**Every contribution passes the same gate:** a coverage's premium counts only when
`PremiumIndicator = 1` **and** `Premium ≠ 0`. A coverage priced at zero and a coverage never
bought are indistinguishable in the total.

---

## 6. What is computed, and what you must supply

| | Computed by ISO's rules | Supplied by the caller |
|---|---|---|
| Prem/Ops, Products, Liquor premium | ✔ | exposures, class code, limits, deductible — and a separate risk for Liquor |
| Med Pay charge | ✔ (as an ILF factor) | the Med Pay **limit** |
| Terrorism premium | ✔ | `TerrorismCoverage` acceptance, or the cap / NBCR endorsement |
| Package / experience / expense mods | — | all four, at policy level |
| Loss cost multiplier | — | the carrier's LCM (the CW tables hold `1`) |
| **Minimum premium top-up** | **nothing** in 2027 (computed in earlier editions — §7) | **the minimum, the comparison and the top-up, all outside ISO's roll-up** |

---

## 7. The same scenario on the edition in force today

Rated at **2026-10-02** (`GL_OK_20261001_V01` over `GL_CW_20261001_V01`), the identical
submission gives **939**, not 852:

| | 2026-10-02 | 2027-04-01 |
|---|---|---|
| Prem/Ops loss cost → `BaseRate` | 0.45 → 0.450 | 0.41 → 0.410 |
| Med Pay | `MedPayFactor` **1.02** for class 10026 (per class, not per type) → separate `MedicalPaymentsCharge` **9**; `FinalILF` 2.010 | factor 1.007 inside `FinalILF` 2.017 |
| Prem/Ops `Premium` | 0.905 × 1,000 + 9 = **914** | **827** |
| Products `Premium` | **21** | **21** |
| Terrorism | 4 + **0** (no $1 floor) | 3 + **1** |
| Minimum-premium records | **compute**: `CoveragePremium` 914 / 21 / Special Combined 935, `MinPremium` 0, top-up 0 | switched off |
| **Total** | **939** | **852** |

Before 2027-04-01 ISO's rules do the minimum-premium work themselves: each policy-level record
sums its coverage across every classification, takes the largest classification minimum and
adds `MinPremium − CoveragePremium` when the minimum is higher. Oklahoma's countrywide minimum
rows for these keys are `0`, so no top-up arises here.

---

## 8. Limits

- **Countrywide edition, one state.** Six GL states rewrite `SetPremium`, all of them terrorism
  (AK, FL, NY, TX, VA, VT) — so a state run of this scenario may price terrorism differently.
  Nothing else in the scenario is state-rewritten.
- **Engine-rated, not ISO-confirmed at 2027-04-01.** The figures are the engine's. The engine
  matches ISO on 50 of 50 standard risks and 184 of 184 varied risks, but all on pre-2027
  editions; the 2027-04-01 numbers await a live call (`docs/PRD-GL-RATING-ENGINE.md` §8, C8).
- **Liquor dollars not shown.** Oklahoma files no liquor rates in the countrywide tables used
  here; see `LiquorLiability_RatingAlgorithms.md` for a rated liquor risk.
- **Conditions flattened.** Each rule's branches are summarised; a live rating takes one path.
