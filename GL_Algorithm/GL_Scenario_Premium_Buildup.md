# A worked scenario — how six coverages become one policy premium

**The risk.** One location, one classification (Mercantile), written on the
*Premises/Operations and Products/Completed Operations* subline, with:

- **Premises/Operations** coverage
- **Products/Completed Operations** coverage
- **Liquor Liability**
- **Medical Payments at $10,000**
- **Terrorism (TRIA) accepted**
- **Minimum premiums** in play

**Source:** `GL CW 20270401 V01`. **Companions:** `GL_Premium_Map.md` (the whole line),
`GL_PremOps_Prods_Premium_Trace.md` (the two core coverages in detail),
`GL_Premium_Tree.html` (navigable).

**Written:** 2026-09-17.

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
FinalILF = round( (CSLILF + MedicalPaymentsFactor − 1) − FinalDeductibleFactor )
```

At **$10,000, Mercantile**, the countrywide factor is **1.007** — so Med Pay adds **0.007 to
the ILF**, roughly a 0.7% uplift on the Premises/Operations rate and nothing else. Contracting
or Servicing pays 1.011 for the same limit.

| Increased Med Pay limit | Most classification types | Contracting or Servicing |
|---|---|---|
| 10,000 | 1.007 | 1.011 |
| 15,000 | 1.011 | 1.017 |
| 20,000 | 1.014 | — |

**Consequences worth knowing.** Med Pay never appears as a line item. It touches
**Premises/Operations only** — not Products, not Liquor. And because it lands inside `FinalILF`,
it is inside the terrorism base too (§4).

---

## 2. The five premiums, and where each is computed

| # | Coverage | DataDef group | Depth | Computed by |
|---|---|---|---|---|
| 1 | Premises/Operations | `GeneralLiabilityClassificationPremOpsCoverage` | 3 | `SetPremium` |
| 2 | Products/Completed Ops | `GeneralLiabilityClassificationProdsCompldOpsCoverage` | 3 | `SetPremium` |
| 3 | Liquor Liability | `GeneralLiabilityClassificationLiquorCoverage` | 3 | `SetPremium` |
| 4 | Terrorism — Prem/Ops | `GeneralLiabilityTerrorismPremOpsCoverage` | **4** | `SetPremium` |
| 5 | Terrorism — Prods/CompldOps | `GeneralLiabilityTerrorismProdsCompldOpsCoverage` | **4** | `SetPremium` |
| (5b) | Terrorism — all other sublines | `GeneralLiabilityTerrorismAllOtherSublineCoverage` | **4** | `SetPremium` — this is where **Liquor's** terrorism charge lands |

Coverages 1–3 are siblings under the classification. The terrorism coverages sit one level
deeper, under a `GeneralLiabilityTerrorism` record that is itself a child of the classification.

### 1–3 share one formula

```
BaseRate  = LossCost × LCM
FinalRate = BaseRate × FinalILF × SizeOfRisk × PackageMod
                     × ExperienceMod × ExpenseMod × ModToUse
Premium   = round( FinalRate × Exposure / 1000 , 0 )
```

Only the field names differ — `PremOpsCovExposure`, `ProdsCompldOpsCovExposure`,
`LiquorExposure`. Liquor has no size-of-risk term.

> **The $1 floor.** If the arithmetic gives 0 while exposure is above 0, `Premium` is forced to
> `1.0`. Zero is reserved for "not covered".

---

## 3. Terrorism is a percentage of the other premiums

This is the part that makes the scenario order-dependent.

`SetClassCoveragePremium` on the terrorism coverage **sums the premiums of the underlying
coverages for that subline** — Prem/Ops, Loss of Electronic Data, Cyber Incident Liability and
the rest — then:

```
Premium = ClassCoveragePremium × TerrorismILF × exposure-class factors
                                × NuclearBiologicalChemicalRadiological factor
```

**So terrorism cannot be computed until coverages 1–3 are final.** It is a charge *on* the
premium, not a parallel one. Three consequences:

1. **The Med Pay uplift is inside the terrorism base.** A higher Med Pay limit raises Prem/Ops,
   which raises `ClassCoveragePremium`, which raises the terrorism charge. The $10,000 election
   costs slightly more than the 0.7% it appears to.
2. **Liquor's terrorism goes to a different record** — `…TerrorismAllOtherSublineCoverage`,
   not the Prem/Ops one.
3. **`TerrorismCoverage` must be accepted at policy level** — `SetPremium` reads it seven
   levels up. Declined, the charge is zero and the record still exists.

---

## 4. Minimum premium — a slot ISO leaves for you to fill

Each of the three coverages owns a minimum-premium lookup — `LookupPremOpsMinPremium`,
`LookupProdsCompldOpsMinPremium`, `LookupLiquorMinPremium`, plus Prem/Ops's
`LookupSpecialCombinedMinPremium`. And there are three dedicated records at **policy level**:

- `GeneralLiabilityPremOpsPremiumToReachMinCoverage`
- `GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverage`
- `GeneralLiabilityLiquorPremiumToReachMinCoverage`

Each is a leaf at depth 1 that **is summed into the account total**.

**But nothing computes what goes in them.** Their rule files hold only `InitializeRuleSet`,
`CalculateTotalPremium`, `SetCoverageOnPolicyIndicator` and `ErcProcess` — no `SetPremium`. The
only write to `Premium` forces it to `0.0` when the coverage is off. The related datadefs
`PremiumToReachMin` and `TotPremiumPriorToMin` are, corpus-wide, **written 0 times and read 0
times**.

> **So ISO gives you the minimum premium, a place to put the shortfall, and a roll-up that will
> add it — but not the comparison in between.** Deciding that the premium fell short, computing
> the top-up and supplying it is the caller's job. A submission that ignores these records
> produces a total with no minimum applied, and nothing flags it.

---

## 5. How it all comes together

```
                                        GeneralLiability.ErcCalculatedTotalPremium   ← POLICY TOTAL
                                                      ▲
        ┌─────────────────────────────────────────────┼──────────────────────────────────┐
        │                                             │                                  │
  PremOpsPremiumToReachMin              GeneralLiabilityLocation                 (400+ other
  ProdsCompldOpsPremiumToReachMin       .ErcCalculatedTotalPremium                policy-level
  LiquorPremiumToReachMin                          ▲  depth 1                     endorsements)
  — depth 1, caller-supplied —                     │
                                       GeneralLiabilityClassification
                                          .ErcCalculatedTotalPremium
                                                   ▲  depth 2
        ┌──────────────┬───────────────┬───────────┴──────────────┐
        │              │               │                          │
   Prem/Ops        Prods/CompldOps   Liquor              GeneralLiabilityTerrorism
   Premium         Premium           Premium                .ErcCalculatedTotalPremium
   depth 3         depth 3           depth 3                      ▲  depth 3
   ▲                                                   ┌──────────┼──────────┐
   │                                              Terr PremOps  Terr Prods  Terr AllOther
   └── Med Pay $10,000 enters here,               depth 4       depth 4     depth 4
       as +0.007 on FinalILF                           (each = ClassCoveragePremium × factors)
```

**Order of computation:**

1. Rate and price Prem/Ops, Products and Liquor — Med Pay's 1.007 is inside Prem/Ops's ILF.
2. Sum those into `ClassCoveragePremium` per subline; compute the three terrorism charges.
3. Roll the terrorism record up into the classification alongside 1–3.
4. Classification → location → policy.
5. **Separately**, the caller compares each subline's premium against its minimum and puts any
   shortfall into the matching `…PremiumToReachMinCoverage` record at policy level, which the
   policy total adds directly.

**Every contribution passes the same gate:** a coverage's premium counts only when
`PremiumIndicator = 1` **and** `Premium ≠ 0`. A coverage priced at zero and a coverage never
bought are indistinguishable in the total.

---

## 6. What is computed, and what you must supply

| | Computed by ISO's rules | Supplied by the caller |
|---|---|---|
| Prem/Ops, Products, Liquor premium | ✔ | exposures, class code, limits, deductible |
| Med Pay charge | ✔ (as an ILF factor) | the Med Pay **limit** |
| Terrorism premium | ✔ | `TerrorismCoverage` acceptance |
| Package / experience / expense mods | — | all four, at policy level |
| Loss cost multiplier | — | the carrier's LCM |
| **Minimum premium top-up** | **the minimum only** | **the comparison and the top-up amount** |

---

## 7. Limits

- **Countrywide.** Six GL states rewrite `SetPremium`, all of them terrorism — so a state run
  of this scenario may price terrorism differently. Nothing else in the scenario is
  state-rewritten.
- **Structural.** Read from rule XML; nothing was rated. No dollar figures are asserted beyond
  the filed Med Pay factors.
- **Conditions flattened.** Each rule's branches are summarised; a live rating takes one path.
