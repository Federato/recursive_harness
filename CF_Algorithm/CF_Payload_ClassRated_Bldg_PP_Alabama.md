# CF rating payload — class-rated Building and Personal Property, Alabama

**Status: derived from ISO's own test cases.** This replaces an earlier draft that was
reasoned from the DataDef schema and the GL payload. That draft got several things wrong;
everything below is now anchored on ISO-authored STC payloads shipped inside the ERC
packages, with the schema used only to explain *why* the shape is what it is.

**Primary sources — ISO STC test cases**
- `CF\20260601\CF AL 20260601 V01\STC\STC_CP000021181.json` — the file you pointed me at.
  Builders Risk, building only, no contents.
- `CF\20230801v2\CF AL 20250201 V01\STC\STC_CP000017321.json` — **class-rated Building
  *and* Personal Property**, Alabama. This is the case that actually matches the task, and
  most of the detail below comes from it.

**Supporting**
- Countrywide package `CFCW20260601V01`; Alabama package `CF AL 20270301 V01`
- `CF_Algorithm/CauseOfLoss_Building_RatingAlgorithms.md`,
  `CauseOfLoss_PersonalProperty_RatingAlgorithms.md`, `CF_RatingPath_Switches.md`

**There are 924 STC payloads across the CF and GL packages, 206 of them containing
Personal Property.** Seven are Alabama. This corpus was not being used; it is the best
available specification of the request format, because ISO wrote it and rates against it.

**Written:** 2026-09-17

---

## 1. The envelope — confirmed

**A live RAaS request has two parts: a `header` carrying account identity, and a `body`
carrying the rating content.** Confirmed 2026-09-17 against the repo's own real GL RAaS
inputs (`Payloads/<STATE>/1. Input.json`), which is where the populated authorization block
lives:

```json
{
  "header": {
    "quoteback": "",
    "authorization": {
      "orgId": "106169",
      "shipId": "106169"
    }
  },
  "body": {
    "SchemeKeys": {
      "ProductName": "Commercial Property AL",
      "EffectiveDateTime": "2027-03-01T00:00:00"
    },
    "CommercialProperty": [ { ... } ]
  }
}
```

**An STC file is the `body` alone.** ISO's shipped test cases start at `SchemeKeys` with no
wrapper, because they are the rating content rather than a transport request. Both facts are
true and it is worth keeping them apart:

| | Carries | Where it comes from |
|---|---|---|
| `header` | `quoteback`, `authorization.orgId`, `authorization.shipId` | the account, not the risk. Same for every request |
| `body` | `SchemeKeys` + the `CommercialProperty` tree | the risk. This is what an STC file contains |

`quoteback` is an empty string in every observed request. `orgId` and `shipId` carry the
same value (`106169`) in this account's inputs — they are not necessarily always equal, so
do not collapse them to one field.

Corrections against my earlier draft:

| Earlier draft | Truth |
|---|---|
| `header` + `body` wrapper around the content | **Half right, and now settled.** The wrapper is real for a live request — see §1. What was wrong was the claim that an STC file has one: it does not, because an STC file *is* the body. |
| `ProductName: "Commercial Property AL"` — guessed | **Confirmed verbatim.** |
| Policy carries `StateCode: "AL"` | **No `StateCode` anywhere in the payload.** State comes from `ProductName`. |
| Policy carries `LossCostMultiplier` | **Absent from every STC.** The field exists on three groups in the DataDef, but ISO's cases don't supply it — it comes from the carrier's ratebook, not the request. |

### The array-vs-object rule, now verified

A child is a **JSON array** if the schema declares an `XTable` element for it, and a
**JSON object** otherwise. I checked this against the STC and it agrees in every case:

| Child | `…Table` in XSD | STC form |
|---|---|---|
| `CommercialPropertyLocation`, `…Structure`, `…OccupClass`, `…PersonalProperty` | yes | `[ … ]` |
| `CommercialPropertyVandalismExclusion`, `…CyberIncidentExclusion`, `…MultipleDeductibleFormFixedDollarDeductibles` | yes | `[ … ]` |
| `CommercialPropertyStructureBuildingBasicGroupICoverage` and all sibling coverage records | **no** | `{ }` |
| `CommercialPropertyPostTRIACoverage`, `…LocationFireDepartmentCharge` | no | `{ }` |

**My earlier skeleton wrote the coverage records as `[{}]`. That is wrong — they are `{}`.**
This is the same singleton-vs-repeating distinction behind the data-dictionary fix earlier
in this session, now confirmed from ISO's side.

---

## 2. The record spine — confirmed

```
CommercialProperty                          policy
└── CommercialPropertyLocation              premises
    └── CommercialPropertyStructure         the building      ← Building rates here
        └── CommercialPropertyOccupClass    occupancy class
            └── CommercialPropertyPersonalProperty            ← Contents rates here
```

Confirmed by the STC nesting. Contents genuinely sits two levels under the building — you
cannot send personal property without a Structure to carry it.

---

## 3. What each level actually carries

Field lists below are the **exact key sets** from `STC_CP000017321.json` (class-rated
Building + PP, Alabama). This is the single most useful correction in the document: far
fewer fields are supplied than the DataDef would suggest, because most rating drivers are
*derived* rather than sent.

### 3.1 `CommercialProperty` — policy (14 scalars)

```
PolicyType            "Commercial Property Policy"   ← the widest-reaching switch
BlktRated             "No"        MUBlktRated        "No"      MUPolicyType   "No"
PackageModFactor      1.0         IRPMApplies        "No"      CPPIRPMFactor  0.0
MultiPremiumAndDispersionCreditFactorUser            0.0
TerrorismIndicator    "Yes"       CoverageForCertifiedActs     "No"
TRIAType              "Is in Effect for the Next 12 Months"
FungusWetRotDryRotBacteriaCov  "15,000 Sub Limit"
EQSubLimitBlktIndicator  "No"     FloodCovEndtBlktIndicator    "No"
```

Children: `CommercialPropertyPostTRIACoverage {}`, `CommercialPropertyTotPremiumCoverage {}`,
`CommercialPropertyCyberIncidentExclusion [{}]`, `CommercialPropertyLocation [ … ]`.

**Note:** `PackageModFactor`, `CPPIRPMFactor` and
`MultiPremiumAndDispersionCreditFactorUser` are *inputs here*. In my earlier draft I listed
these as untraced factors that stopped me computing a premium. They are not derived — the
submitter supplies them.

### 3.2 `CommercialPropertyLocation` — premises (15 scalars)

```
UnitNumber       1
ZipCode          "08003"     City    "Birmingham"     County  "Autauga"
ProtectClass     "1"                         ← NOT "ProtectionClass"
BasicGroupIRatingTerr              "Birmingham"
BasicGroupIIRatingTerr             "Inland Territory"
SpecialRatingTerr                  "Remainder of State"
EQTerr           "1"        TerrorismTerritory  "Statewide"
GeographicWindHazardLevelTerritory "Autauga"
EQCauseOfLossForm   "Earthquake Form (CP 10 28)"
FloodCovIndicator "No"   OperationalUnitIndicator "No"
MultipleResidentialPropSpecialCredit "No"
```

Two findings here:

1. **`ProtectClass`, not `ProtectionClass`.** Both names exist in the DataDef on Location —
   `ProtectClass` is what the payload uses. Getting this wrong fails silently.
2. **Territories are supplied, not derived.** Open item 5 in the earlier draft is closed,
   and the evidence is unusually clean: ISO's own fixture pairs `ZipCode "08003"` (a New
   Jersey ZIP) with `City "Birmingham"` and `County "Autauga"` — and the 20260601 case pairs
   ZIP 35004 (Moody, AL) with Birmingham/Autauga. Birmingham is in Jefferson County. **The
   geography in these fixtures is internally inconsistent and ISO still rates them**, which
   is only possible if `BasicGroupIRatingTerr` and its siblings are taken at face value.
   Do not expect the engine to derive territory from an address.

### 3.3 `CommercialPropertyStructure` — the building (43 scalars)

The class-rating essentials, as actually sent:

```
RatingType        "Class"            ClassCode    "0074"
ConstructionType  "Frame"            ← a *detailed* type; the code is derived in 2 hops (§6.3)
CovType           "Building"         CauseOfLoss  "Special"
CovForm           (absent here — set on OccupClass)
Limit             450000             FullBldgValue  550000
Coinsurance       "80%"              Deductible   "1,000"
ValuationType     "Actual Cash Value"
IncludedInBlkt    "No"               VacantBuilding "No"
SprinklerSystem   "None"             RatingTypeBasicGroupII "Class"
ClassificationDescription  "Boarding and Lodging Houses, … Up to 10 Units"
NumStories "1-3"  YearOfConstructionCode 2000   OpenSides "No"
BCEG "Ungraded"   BCEGClass "Not Graded"
TheftDeductible "2,500"   WindstormOrHailDeductible "Not Applicable"
RoofLevel / RoofSubDecking / AgeOfTheRoof / CertificateType / CertificateLevel
SpecificGroupIRate 0.0    (present but zero on a Class risk)
EQ*: EQDeductible, EQCoinsurance, EQCovIndicator, EQClass, EQSprinklerLeakageOnly
SoftStory "Yes"   RentalProperty "No"   PublicInstitutionalPlanApply "No"
InflationGuard / AgreedValueOption / ConformsToCondoActs / TerrorismOverride / TerrorismSubLimit
InsuredHoldsAnIBHSHurricaneCertificateOrAnIBHSHighWindAndHailCertificate
UnitNumber 1
```

**`ConstructionType` is the input; `ConstructionCode` is derived — in two hops, not one.**
This is easy to get wrong, because the second hop's table has only six rows and looks like
the whole story:

```
ConstructionType        (payload — 25 detailed values)
   ↓  ConstructionTypeToUse rate table, keyed StateCode + ConstructionTypeBldg
ConstructionTypeToUse   (6 values)
   ↓  ConstructionCode rate table, keyed StateCode + ConstructionTypeToUse
ConstructionCode        (1–6)
```

`SetConstructionCode` (`CommercialPropertyStructureRules.Rule.xml`, line 1041) delegates to
`LookupConstructionCode`; `LookupConstructionTypeToUse` performs the first hop. Both are
state-first with `CW` fallback, and no state overrides either table.

**Hop 2** — the six-row table everyone finds first:

| `ConstructionTypeToUse` | Code |
|---|---|
| Frame | **1** |
| Joisted Masonry | **2** |
| Non-Combustible | **3** |
| Masonry Non-Combustible | **4** |
| Modified Fire Resistive | **5** |
| Fire Resistive | **6** |

**Hop 1** is the one that matters for building a payload. `ConstructionTypeToUse` collapses
**25 detailed construction types** onto those six. The payload sends the *detailed* value:

| Sent in `ConstructionType` | Collapses to |
|---|---|
| `Frame` | Frame |
| `Joisted Masonry - Reinforced` · `- Other Than Reinforced` (± `- Superior Roofing`) | Joisted Masonry |
| `Non-Combustible - Light Steel` · `- Other Than Light Steel` (± `- Superior Roofing`) | Non-Combustible |
| four `Masonry Non-Combustible - …` variants (± `- Superior Roofing`) | Masonry Non-Combustible |
| four `Modified Fire Resistive - …` variants | Modified Fire Resistive |
| four `Fire Resistive - …` variants | Fire Resistive |

`Frame` is the only value that is legal at *both* hops, which is why a payload using it
still works if you assume a single hop — and why the mistake survives testing. The
`- Superior Roofing` variants are also what drive `SuperiorRoofingIndicator` in the Basic
Group II chain (§7).

The STC corpus sends 8 distinct values: `Frame` (345 of 364), then
`Modified Fire Resistive - Other Than Reinforced Masonry - Light Steel`,
`Joisted Masonry - Other Than Reinforced`, `Joisted Masonry - Reinforced`,
`Fire Resistive - Other Than Reinforced Masonry - Light Steel`,
`Non-Combustible - Light Steel`, `Fire Resistive`, and one `Entirely Metal` — the last of
which is **not in the countrywide 25**, so at least one more value exists somewhere.

This also explains why `DomainConstructionCode` is empty in every package — the mapping
lives in *rate* tables, not a domain list, because it is a derivation and not a pick-list.

Also note `TotAmtInsurance` is **not sent** — `FullBldgValue` and `FullPrsnlPropValue` are,
and the total is derived. My earlier draft listed `TotAmtInsurance` as a payload field.

All eighteen `…Coverage` children are sent as empty objects `{}` — the engine fills them.

### 3.4 `CommercialPropertyOccupClass` — occupancy class (8 scalars)

```
ClassCode     "0074"
OccupCategory "Residential Apartments and Condominiums"
ClassDesc     "Boarding and Lodging Houses, … Up to 10 Units"
CovForm       "Building and Personal Property Coverage Form"   ← set HERE
SprinklerSystem "None"    TheftDeductible "2,500"
PublicInstitutionalPlanApply "No"    ConformsToCondoActs "Not Applicable"
```

**`Group` and `BldgClassCode` are not sent.** My earlier draft had both as payload fields
on OccupClass and on Personal Property. They are derived, and `SetGroup`
(`CommercialPropertyOccupClassRules.Rule.xml`, line 640) confirms exactly how — a 17 KB
`Choose` that reads **only three values**: `RatingType`, `ClassCodeToUse` and `ClassCode`,
and assigns one of `A`, `B`, `C` or `Not Applicable`.

The logic is the two-key mechanism the AL rate table implies:

- `RatingType ≠ "Class"` → `Not Applicable`, immediately.
- `ClassCodeToUse` (the *building's* class code, carried down from Structure) must be one
  of the ten eligible codes — otherwise `Not Applicable`.
- The OccupClass's own `ClassCode` then selects `A`, `B` or `C`.

So the gate and the selector are two different class codes at two different levels. You
supply both as `ClassCode` on Structure and on OccupClass; the engine does the rest.

`CovForm` is set once here and inherited downward, as `CF_RatingPath_Switches.md` warned.
Do **not** also set it on Personal Property — the STC doesn't.

### 3.5 `CommercialPropertyPersonalProperty` — contents (16 scalars)

```
CovType        "All Personal Property"     ← a value universe I did not have before
CauseOfLoss    "Special"
Limit          650000        FullPrsnlPropValue  750000
Coinsurance    "80%"         ValuationType "Actual Cash Value"
IncludedInBlkt "No"          UnitNumber 1
AgreedValueOption "No"       InflationGuard "Not Applicable"
EQCoinsurance / EQCovIndicator / EQGrade / EQSprinklerLeakageOnly
TerrorismOverride "No"       TerrorismSubLimit 0
```

This is the biggest correction in the document. Personal Property **does not carry**
`RatingType`, `ClassCode`, `BldgClassCode`, `Group`, `ConstructionType`, `Deductible`,
`ProtectClass` or `SprinklerSystem`. Every one of those is inherited from OccupClass,
Structure or Location. My earlier §4.5 listed them as PP payload drivers; that was wrong.

Contents carries only: what it is, what it's worth, its limit, its coinsurance, its cause
of loss, and its valuation.

---

### 3.6 Validated against all 7 Alabama STC cases

The field lists above came from 2 cases. Aggregating all 7 AL STC payloads (7 policy
records, 7 locations, 7 structures, 4 occupancy classes, 4 personal property records)
confirms a stable mandatory core plus a small conditional set:

| Level | Distinct scalars seen | Present in **every** record | Conditional |
|---|---|---|---|
| `CommercialProperty` | 14 | **14** | none |
| `CommercialPropertyLocation` | 16 | 15 | 1 |
| `CommercialPropertyStructure` | 49 | 38 | 11 |
| `CommercialPropertyOccupClass` | 8 | **8** | none |
| `CommercialPropertyPersonalProperty` | 16 | 14 | 2 |

Policy and OccupClass are fully stable — every field appears in every case. The
conditional fields, with how often they appear:

| Field | Level | Frequency | Reading |
|---|---|---|---|
| `ConstructionCode` | Structure | **1 / 7** | **Can be supplied directly as an override.** `SetConstructionCode` assigns only when null, so a caller may bypass the `ConstructionType` lookup. |
| `SubStdConditionA`–`E` | Structure | 2 / 7 | Only on substandard-condition risks |
| `EQClass`, `EQDeductible` | Structure | 3 / 7 | Only when earthquake coverage is elected |
| `SoftStory` | Structure | 3 / 7 | Earthquake-related |
| `FullBldgValue` | Structure | 5 / 7 | Not universally required |
| `TerrorismSubLimit` | Structure | 5 / 7 | |
| `FungusWetRotDryRotBacteriaCovLocApply` | Location | 3 / 7 | |
| `EQGrade`, `FullPrsnlPropValue` | PersonalProperty | 3 / 4 | |

The 14 policy-level and 8 OccupClass fields should be treated as **required**; everything
in the conditional table is coverage-dependent.

---

### 3.7 The Personal Property `CovType` universe

`DomainCovTypePrsnlProp` offers **16 distinct values**, keyed `StateCode + PolicyType +
CovForm` — so the legal list changes with both the policy type and the coverage form:

| CovForm | Values offered |
|---|---|
| Building and Personal Property Coverage Form | All Personal Property · All Other Personal Property · Contents Except Stock · Stock · Furniture · Fixtures · Machinery and Equipment · Property of Others · Non-Owned Trailers · Tenants Improvements and Betterments · Valuable Papers and Records – Other Than Electronic Data · Personal Property in a Vault with an Approved Fire Rating · Property Other than Categories Listed Above |
| Condominium Commercial Unit Owners | as above, but `Fixtures, Improvements and Alterations` replaces `Fixtures` / `Tenants I&B` |
| Condominium Association | `All Personal Property` only (CPP) / `All Other Personal Property` only (SPP) |
| Legal Liability | `Personal Property of Others` · `Non-Owned Trailers` |
| Tobacco Sales Warehouse | `All Personal Property` only |
| Class Rated Building Only, No Personal Property | `Not Applicable` |

**Only three of the sixteen change rating.** Every other value reaches nothing but
`DoMessage*` validation rules and `AttachForm*` form-attachment rules:

| Value | Effect |
|---|---|
| `Valuable Papers and Records - Other Than Electronic Data` | Tested 7 times — in `SetBasicGroupICauseOfLossAdjustment`, `SetBasicGroupIICauseOfLossAdjustment` and `SetBroadRate`. The most rating-consequential contents value |
| `Personal Property in a Vault with an Approved Fire Rating` | Gates `SetFireSafeVaultFactor`, itself gated on `RatingType = "Class"` |
| `Tobacco Sales Warehouses` | Guards the LOI factors — **but see below** |

> **A dead test.** `SetBasicGroupILOIFactor`, `SetBasicGroupIILOIFactor` and
> `SetBroadLOIFactor` each guard on `CovType <> "Tobacco Sales Warehouses"`. That exact
> string is offered by **zero rows** in `DomainCovTypePrsnlProp` across **all 23 packages
> that file it**, at any of its 16 values — the Tobacco form's contents value is
> `All Personal Property`. So the guard can never be false and the branch is unreachable
> through this field. Tobacco warehouses are still ratable, via the `CovForm` and the
> `CommercialPropertyPersonalPropertyTobaccoSalesWarehousesCoverage` record — just not by
> this route. Treat the constant as legacy, not as a value to support.

The STC corpus uses **`All Personal Property` and nothing else**, across all 364 CF cases.
Fifteen of the sixteen values have no ISO-authored example anywhere.

---

## 4. Alabama rating data (unchanged — this part held up)

AL files its own class base rates: **`BasicGroupIRate`, 1,368 rows**, keyed
`StateCode, ClassCode, ConstructionCode, Group, CovType`, shared between Building and
Contents with `CovType` separating them (`Building` 624 rows, `PersProp` 744).

Group A/B/C is open to only ten building class codes — `0321, 0322, 0323, 0341, 0342,
0343, 0581, 0582, 0701, 0702`. `YARD` is open to `1400, 1650, 1700` at construction 1 and 3
only. Everything else rates at `Group = "Not Applicable"`. Since `Group` is derived, this
is a fact about what the engine will produce, not about what you send.

Building and Contents **do not share a territory input in Alabama**:

| | Table | Key | AL values |
|---|---|---|---|
| Building | `RatingTerritoryGroupIFactor` | `BasicGroupIRatingTerr` (city) | Birmingham 2.162, City of Mobile 0.674, Balance of State 1.0 |
| Contents | `PrsnlPropTerrMultiplier` | `SpecialRatingTerr` (county) | Jefferson 1.37, Mobile 1.192, Remainder of State 1.0 |

The STC bears this out — it sends `BasicGroupIRatingTerr: "Birmingham"` and
`SpecialRatingTerr: "Remainder of State"` on the same location. Those are not in conflict;
they are two different axes.

Also AL-filed and on this path: `DeductibleFactor` (462 rows), `BuildingHeightFactor` (216),
`OccupancyType` (154), `VacantBldgPreviousOrIntendedOccup` (106), `BCEGFactor` (36),
`SubStdConditionRate` (30), `BasicGroupIILOIFactorBldg`/`…PersProp`,
`BaseRateAdjustmentFactor` (BGI 0.8, BGII 0.75). AL does **not** file
`ProtectionClassFactor` or `BasicGroupILOIFactorBldg` — those resolve countrywide, state
first with CW as fallback.

---

## 5. Reference payload

> **A ready-to-use file:** `CF_Algorithm/sample_payloads/AL_class_rated_bldg_pp_special.json`
> — Special form, class-rated Building + Personal Property, Alabama. Every one of its 96
> scalar fields was checked against the data dictionary for existence on its group, every
> child record against the schema's array-vs-object rule, and every enum against Alabama's
> own domain lists. The inline payload below is the Basic-form variant.

Class-rated Building + Personal Property, Alabama — the shape of `STC_CP000017321.json`,
trimmed to the fields that matter for the two coverages and with the class changed to
`0701` so the Group A/B/C mechanism is live.

```json
{
  "SchemeKeys": {
    "ProductName": "Commercial Property AL",
    "EffectiveDateTime": "2027-03-01T00:00:00"
  },
  "CommercialProperty": [{
    "PolicyType": "Commercial Property Policy",
    "BlktRated": "No",
    "MUBlktRated": "No",
    "MUPolicyType": "No",
    "PackageModFactor": 1.0,
    "IRPMApplies": "No",
    "CPPIRPMFactor": 0.0,
    "MultiPremiumAndDispersionCreditFactorUser": 0.0,
    "TerrorismIndicator": "Yes",
    "CoverageForCertifiedActs": "No",
    "TRIAType": "Is in Effect for the Next 12 Months",
    "FungusWetRotDryRotBacteriaCov": "15,000 Sub Limit",
    "EQSubLimitBlktIndicator": "No",
    "FloodCovEndtBlktIndicator": "No",
    "CommercialPropertyPostTRIACoverage": {},
    "CommercialPropertyTotPremiumCoverage": {},
    "CommercialPropertyCyberIncidentExclusion": [{}],

    "CommercialPropertyLocation": [{
      "UnitNumber": 1,
      "City": "Birmingham",
      "County": "Jefferson",
      "ZipCode": "35203",
      "ProtectClass": "1",
      "BasicGroupIRatingTerr": "Birmingham",
      "BasicGroupIIRatingTerr": "Inland Territory",
      "SpecialRatingTerr": "Jefferson",
      "TerrorismTerritory": "Statewide",
      "FloodCovIndicator": "No",
      "OperationalUnitIndicator": "No",
      "MultipleResidentialPropSpecialCredit": "No",
      "CommercialPropertyLocationFireDepartmentCharge": { "FireIncreaseLimitApplyOnPolicyIndicator": "No" },
      "CommercialPropertyLocationNewlyAcquiredLocationTimeElement": { "Indicator": "No" },

      "CommercialPropertyStructure": [{
        "RatingType": "Class",
        "RatingTypeBasicGroupII": "Class",
        "ClassCode": "0701",
        "ConstructionType": "Frame",
        "CovType": "Building",
        "CauseOfLoss": "Basic",
        "Limit": 500000,
        "FullBldgValue": 550000,
        "Coinsurance": "80%",
        "Deductible": "1,000",
        "ValuationType": "Actual Cash Value",
        "IncludedInBlkt": "No",
        "VacantBuilding": "No",
        "SprinklerSystem": "None",
        "OpenSides": "No",
        "NumStories": "1-3",
        "YearOfConstructionCode": 2000,
        "BCEG": "Ungraded",
        "BCEGClass": "Not Graded",
        "TheftDeductible": "2,500",
        "WindstormOrHailDeductible": "Not Applicable",
        "UnitNumber": 1,
        "SpecificGroupIRate": 0.0,

        "CommercialPropertyStructureBuildingBasicGroupICoverage": {},
        "CommercialPropertyStructureBuildingBasicGroupIICoverage": {},
        "CommercialPropertyStructureBuildingBroadCoverage": {},
        "CommercialPropertyStructureBuildingSpecialCoverage": {},

        "CommercialPropertyOccupClass": [{
          "ClassCode": "0701",
          "CovForm": "Building and Personal Property Coverage Form",
          "OccupCategory": "Residential Apartments and Condominiums",
          "SprinklerSystem": "None",
          "TheftDeductible": "2,500",

          "CommercialPropertyPersonalProperty": [{
            "CovType": "All Personal Property",
            "CauseOfLoss": "Basic",
            "Limit": 150000,
            "FullPrsnlPropValue": 175000,
            "Coinsurance": "80%",
            "ValuationType": "Actual Cash Value",
            "IncludedInBlkt": "No",
            "AgreedValueOption": "No",
            "InflationGuard": "Not Applicable",
            "UnitNumber": 1,

            "CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage": {},
            "CommercialPropertyPersonalPropertyPrsnlPropBasicGroupIICoverage": {},
            "CommercialPropertyPersonalPropertyPrsnlPropBroadCoverage": {},
            "CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverage": {}
          }]
        }]
      }]
    }]
  }]
}
```

Filed AL values this resolves to. `ConstructionType: "Frame"` derives
`ConstructionCode = 1`, and `ProtectClass: "1"` gives protection class 1:

| Lookup | Value |
|---|---|
| `BasicGroupIRate` AL / 0701 / **1** / Not Applicable / Building | **0.115** |
| `BasicGroupIRate` AL / 0701 / **1** / B / PersProp | **0.187** |
| (Group A would be 0.126, Group C 0.146 — same class, same construction) | |
| `RatingTerritoryGroupIFactor` AL / Birmingham | **2.162** |
| `PrsnlPropTerrMultiplier` AL / Jefferson | **1.37** |
| `ProtectionClassFactor` CW / PC 1 / constr 1 | **0.88** |
| `DeductibleFactor` AL / 1,000 / 175k–500k / Basic Group I | **0.99** |
| `CoinsuranceFactor` CW / 80% | **1.0** |

---

## 6. Derivation chains — traced

### 6.1 Class codes

Four class-code datadefs exist across three levels. All are derived from the two
`ClassCode` values the payload supplies (one on Structure, one on OccupClass):

| Level | Field | Rule | Resolves to |
|---|---|---|---|
| Structure | `ClassCodeToUse` | `SetClassCodeToUse` (Structure line 893) | plain copy of `ClassCode` — nothing else |
| OccupClass | `BldgClassCode` | `SetBldgClassCode` (OccupClass line 569) | copy of `../../ClassCode` — the **building's** code |
| OccupClass | `ClassCodeToUse` | `SetClassCodeToUse` (OccupClass line 622) | `RatingType = "Class"` → `BldgClassCode`; else own `ClassCode` |
| PersonalProperty | `BldgClassCode` | `SetBldgClassCode` (PP line 1147) | copy of `../../BldgClassCode` |
| PersonalProperty | `ClassCode` | `SetClassCode` (PP line 1209) | copy of `../../ClassCodeToUse` |
| PersonalProperty | `ClassRatedClassCode` | `SetClassRatedClassCode` (PP line 1173) | copy of `../../../../ClassCode` (Structure's), **only when null** — preserves an override |

> **Correction.** I previously wrote that `VacantBuilding = "Yes"` substitutes class code
> `1180` into the rating path. It does not. `1180` appears exactly three times in the
> rules: `SetClassCodeForStat` assigns it to **`ClassCodeForStat`** — a *statistical*
> reporting code, not a rating key — and it is passed as a hardcoded argument to the
> vandalism-factor lookup. `ClassCodeToUse` has no vacancy branch at all; vacancy enters
> the Basic Group I rate through the additive `VacantBuildingRate` term instead.

### 6.2 `Group` — two rules at two levels

`Group` is set **twice**, and the second can override the first:

1. **`SetGroup` on OccupClass** (line 640) — reads `RatingType`, `ClassCodeToUse`,
   `ClassCode`. Assigns `A`, `B`, `C` or `Not Applicable`. Never assigns `YARD`.
2. **`SetGroup` on PersonalProperty** (line 1640) — reads `../../Group`, `BldgClassCode`
   and `YardPropertyIndicator`. Assigns **`YARD`** when `BldgClassCode` is one of
   `1400`, `1650`, `1700` **and** `YardPropertyIndicator` is
   `Yard Property - Combustible` or `Yard Property - Non Combustible`. Otherwise it
   inherits the occupancy class's value.

So `YardPropertyIndicator` **is a payload input** on the Personal Property record, and it
is the only way YARD rating is reachable. Combustible forces `ConstructionCode = 1`,
non-combustible forces `3` — which is exactly why AL files YARD rows at construction 1 and
3 only.

---

## 7. Basic Group II

BGII is a structurally different animal from BGI, and it is where Alabama's state content
is heaviest.

**BGI rates off class code + construction code. BGII rates off rating territory +
construction symbol.** Territory is a *lookup key into the base rate table*, not a
multiplier — there is no BGII analogue to `RatingTerritoryGroupIFactor`.

### 7.1 Extra payload drivers BGII needs

| Field | Level | Role |
|---|---|---|
| `BasicGroupIIRatingTerr` | Location | **A base-rate key.** AL: `Inland Territory` / `Seacoast Territory` / `Beach Territory`, assigned by county via `DomainBasicGroupIIRatingTerrAL` (71 rows). Baldwin County can be any of the three. |
| `ConstructionType` + `NumStories` | Structure | Together resolve `BasicGroupIISymbol` via `LookupBasicGroupIIConstructionSymbol`. AL symbols: `AA`, `A`, `AB`, `B`. |
| `RatingTypeBasicGroupII` | Structure | Separate from `RatingType`. AL narrows it to `Class` / `Specific` — **no `Tentative`**. |
| `OpenSides` | Structure | With `ClassCodeToUse`, drives `BasicGroupIINumericValue`. |
| `BCEG`, `BCEGClass` | Structure | Drive `BCEGFactor` (36 AL rows). BGII only — absent from the BGI rate. |
| `WindstormOrHailDeductible` | Structure | AL files `WindstormOrHailDeductibleFactor` (24 rows). |
| `RoofLevel`, `RoofSubDecking`, `AgeOfTheRoof`, `CertificateType`, `CertificateLevel`, `InsuredHolds…IBHS…Certificate` | Structure | Roof surfacing and windstorm loss-mitigation credits — AL files three `WindstormLossMitigationCredits` tables. |
| `CommercialPropertyWindstormOrHailExclusion` | Structure child record | An **election**, not a value. Its presence switches the whole rate onto the `LowestBasicGroupIIRate` path. |

### 7.2 Alabama BGII base rates (filed, `CovType` splits Bldg/PersProp)

| Territory | AA | A | AB | B |
|---|---|---|---|---|
| Inland — Bldg | 0.080 | 0.091 | 0.115 | 0.156 |
| Inland — PersProp | 0.071 | 0.080 | 0.098 | 0.125 |
| Seacoast — Bldg | 0.288 | 0.321 | 0.384 | 0.684 |
| Seacoast — PersProp | 0.212 | 0.235 | 0.304 | 0.534 |
| Beach — Bldg | 0.492 | 0.546 | 0.668 | 1.145 |
| Beach — PersProp | 0.337 | 0.374 | 0.496 | 0.875 |

Seacoast is roughly 3.5× Inland and Beach roughly 6× — so `BasicGroupIIRatingTerr` is the
single most consequential field in an Alabama BGII payload.

### 7.3 A filed-data defect in the current AL edition

> **`LowestBasicGroupIIRate`, symbol `A`, `PersProp`, is `0.8` in `CF AL 20270301 V01`.
> It was `0.08` in all seven prior AL editions, and every other symbol in the table still
> matches its Inland Territory rate exactly.**

| Symbol | Lowest (20270301) | Inland PersProp | Prior editions |
|---|---|---|---|
| AA | 0.071 | 0.071 | 0.071 ✓ |
| **A** | **0.8** | **0.08** | **0.08** ← 10× jump |
| AB | 0.098 | 0.098 | 0.098 ✓ |
| B | 0.125 | 0.125 | 0.125 ✓ |

This reads as a decimal-place error in ISO's newest Alabama filing. **Impact:** a
class-rated personal property risk with a windstorm/hail exclusion and construction symbol
A, in Alabama, at the current edition, rates its BGII contents roughly 10× too high —
because the exclusion branch rebuilds the rate from `LowestBasicGroupIIBaseRate` instead of
the territory rate.

I swept all 48 states' latest packages for the same shape. Only two other rows sit above
their cheapest territory rate — Maine's `A` and `AB` PersProp (0.03 vs 0.028, 0.033 vs
0.032). Those are small enough to be a deliberately filed floor rather than an error;
Alabama's is a 10× jump that also breaks its own edition history. **Do not code around
this** — it should be raised with ISO. Logged for the simplifications/divergence backlog.

---

## 8. Broad and Special

These two are where the ISO fixtures actually live — 357 of 364 CF payloads are Special,
19 are Broad. They are also the two simplest chains, and they key on things Basic does not.

### 8.1 Broad — the shortest chain

Six steps, and **no cause-of-loss adjustment rule at all** — the only one of the four forms
without one. No territory, no protection class, no symbol.

`BroadFormBaseRate` is keyed `StateCode + ConstructionTypeToUse + CovType`, where `CovType`
here is the lookup's own parameter (`Bldg` / `BldrRisk` / `PersProp`), not the record's
field. **Alabama does not file it — it resolves countrywide:**

| ConstructionTypeToUse | Bldg | BldrRisk | PersProp |
|---|---|---|---|
| Frame / Joisted Masonry / Non-Combustible / Masonry Non-Combustible | 0.015 | 0.012 | 0.021 |
| Modified Fire Resistive / Fire Resistive | 0.010 | 0.012 | 0.011 |

So Broad is effectively two-tiered on construction, and Builders Risk is flat. Class code
matters only in one place: `ClassCodeToUse = "1150"` switches the lookup to the `BldrRisk`
row.

**Payload drivers Broad needs beyond the shared set:** nothing new. `ConstructionType`
and `ClassCode` already carry it.

### 8.2 Special — Building is flat, Contents is not

**Building.** `SpecialBuildingRate` is a *flat statewide constant* — keyed
`StateCode + Constant`, one row per state. Alabama files **0.039**. No class code, no
construction, no territory, no protection class. The entire Building Special rate is
`0.039 × LCM`, then theft / roof / coinsurance / LOI / deductible factors.

**Contents is the odd one out in the whole line.** `SpecialPrsnlPropRate` is keyed
`StateCode + OccupCategory + OccupCategorySeverity` — **an occupancy axis no other form
uses.** Alabama, 13 rows:

| OccupCategory | Severity | Rate | Theft-excl factor |
|---|---|---|---|
| Residential Apartments and Condominiums | Not Applicable | 0.116 | 0.6 |
| Offices | Not Applicable | 0.093 | 0.4 |
| Mercantile | High / Medium / Low | 0.139 / 0.129 / **0.092** | 0.4 |
| Motels and Hotels | Not Applicable | 0.065 | 0.6 |
| Institutional | High / Low | 0.065 / 0.038 | 0.4 |
| Industrial and Processing | High / Low | 0.149 / 0.130 | 0.4 |
| Service | High / Low | 0.105 / 0.087 | 0.4 |
| Contractors | Not Applicable | 0.191 | 0.2 |

`SpecialPrsnlPropTheftExclusionFactor` is keyed on `OccupCategory` alone — no severity.

### 8.3 Two payload fields Basic never needed

| Field | Level | Note |
|---|---|---|
| `OccupCategory` | OccupClass **and** PersonalProperty | Declared on both. The Special Contents rate key |
| `OccupCategoryRiskSeverity` | OccupClass **and** PersonalProperty | `High` / `Medium` / `Low` / `Not Applicable`. **No domain table constrains it** — the legal values are only discoverable from the rate table |

> **Naming trap.** The datadef field is **`OccupCategoryRiskSeverity`**. The rate-table
> column is **`OccupCategorySeverity`**. They are different strings; the lookup binds
> positionally, not by name. Searching the rules for the column name returns nothing —
> which is exactly the wrong conclusion.

> **A real gap in ISO's own fixtures.** `OccupCategoryRiskSeverity` appears in **zero of
> the 364 CF STC payloads** — yet 6 cases use `OccupCategory = "Mercantile"`, and all 6 are
> in states that file three distinct Mercantile severity rows:
>
> | State | High | Medium | Low |
> |---|---|---|---|
> | CO | 0.267 | 0.239 | 0.135 |
> | ME | 0.156 | 0.152 | 0.094 |
> | MI | 0.389 | 0.366 | **0.204** |
> | NM | 0.221 | 0.178 | 0.141 |
>
> Michigan's spread is **~1.9×**. Either the engine applies a default severity that is not
> written down, or ISO's fixtures are underspecified for Special Contents on any
> multi-severity occupancy. Whichever it is, a submission builder must supply this field
> and cannot learn its legal values from a domain list or from an example. Resolve it
> before trusting any Special Contents premium on Mercantile, Institutional, Industrial
> and Processing, or Service.

---

## 9. Does Alabama generalise? The second-state test

Alabama is a "single base-rate table" state, which turns out to be the common case but not
the only one. Two questions were worth testing: does the **base-rate lookup** keep the same
shape in other states, and does the **occupancy-severity** axis found in §8 generalise?

### 9.1 Three different Basic Group I base-rate mechanisms

Counting the latest package of every jurisdiction:

| Mechanism | States | Tables |
|---|---|---|
| Single table | **43** | `BasicGroupIRate` |
| District I / II | **2** — AK, CA | `BasicGroupIDistrictIRate` + `BasicGroupIDistrictIIRate` |
| NYC split | **1** — NY | `BasicGroupIRate` + `BasicGroupIRateNYC` |
| None filed | 2 — CW, PR | — |

Every variant keeps the **same five keys** (`StateCode, ClassCode, ConstructionCode, Group,
CovType`) and the same row count shape — AK and CA file 1,368 rows in *each* district table,
NY 1,308 in each. So the lookup signature does not change; only *which table* is read.

### 9.2 The selector differs in all three — and only California adds a payload field

Each state overrides `SetBasicGroupIBaseRate` with its own selector:

| State | Reads | Rule |
|---|---|---|
| **CA** | **`../../District`** — a Location field | `District I` → District I table, `District II` → District II table |
| **AK** | `BasicGroupIRatingTerr` | territory in `020, 040, 050, 100` → one district, else the other |
| **NY** | `BasicGroupIRatingTerr` | territory in `030, 240, 310, 410, 430` → the NYC table, else the plain one |

**This is the payload consequence, and it is the whole answer to "does Alabama generalise".**
California requires one field Alabama never sends — `District` on
`CommercialPropertyLocation`, values `District I` / `District II`, from `DomainDistrict`
(2 rows, CA only). Alaska and New York require **nothing new**: both derive the split from
`BasicGroupIRatingTerr`, which every payload already carries.

So the answer is: **the record shape holds; one state adds one field.** The three are not
one mechanism — they are three — and only one of them touches the request.

**What New York's five codes actually are.** `030, 240, 310, 410, 430` are not arbitrary:
in NY's `RatingTerrGroupICode` table (keyed `CityTown + County`) they map one-to-one to
**Bronx, Kings, New York, Queens and Richmond** — the five boroughs — each filed with
`CityTown = "Remainder of State"`. So the real determinant is **county**, and the territory
code is the county's proxy.

This matters for the payload. `BasicGroupIRatingTerr` is *supplied*, not derived (§3.2), so
whoever builds the request has to put the right borough code in it. Deriving that code from
a Territory dropdown (`Buffalo` / `Rochester` / `Albany` / `New York City` /
`Remainder of State`) is **not** equivalent — the filed table lets `New York City` pair with
any NY county. A risk in Brooklyn submitted with a non-borough territory code rates off the
wrong table entirely, and nothing errors.

### 9.3 Two dead artefacts found while checking

- **`DomainDistrict` in Alaska is header-only — 0 rows — in all 9 AK editions**, keyed on
  `BasicGroupIRatingTerr`. It is a dropdown that offers nothing, for a field AK's rules never
  read. CA files 2 rows in every edition; no other state files the table at all.
- **`BasicGroupIDistrictTerritory`** is declared on `CommercialPropertyLocation` countrywide
  and is read by **no rule in the countrywide ruleset**. A declared field with no consumer.

Neither should be sent. Both are the kind of thing that looks like a required input if you
read the DataDef instead of the rules.

### 9.4 The severity axis generalises completely

`SpecialPrsnlPropRate` is filed by **45 of 47 jurisdictions** — countrywide is empty, so
Special Contents is entirely state-filed. Across all 45, the severity structure is
**identical**; only the rates differ:

| OccupCategory | Severities — same in all 45 states |
|---|---|
| Mercantile | High · Medium · Low |
| Institutional · Industrial and Processing · Service | High · Low |
| Offices · Residential Apartments and Condominiums · Motels and Hotels · Contractors | Not Applicable |

**This strengthens the §8.3 finding rather than softening it.** `OccupCategoryRiskSeverity`
is not an Alabama quirk — it is required in 45 states, on four occupancy categories, and it
is absent from all 364 ISO fixtures and constrained by no domain table anywhere.

Two jurisdictions differ:

- **Florida** splits Special into Residential and NonResidential tables.
  `SpecialPrsnlPropRateResidential` is a flat constant (0.125); `…NonResidential` is the
  standard `OccupCategory + OccupCategorySeverity` table, minus the Residential category.
  So FL still needs severity — just partitioned. Building splits the same way
  (`SpecialBuildingRateResidential` 0.030).
- **Puerto Rico** files `SpecialPrsnlPropExclgTheftBaseRate` instead, a different structure
  again. PR is outside the ISO-comparison scope, so this is noted, not pursued.

---

## 10. What is still open

1. ~~**`LossCostMultiplier` sourcing**~~ — **decided 2026-09-17: default to `1.0`.**
   LCM appears in no STC payload, and at `1.0` the filed ISO loss cost passes through
   unchanged, which is the correct baseline for proving the engine against ISO. A carrier
   LCM will be a **configured input, by line of business**, not a submission field — see
   Set 6 in the completion tracker. Until that exists, every rate in this document is an
   ISO loss cost, not a carrier rate.

   > **Read every worked number here as LCM = 1.0.** `BasicGroupIRate` multiplies the base
   > rate by `LossCostMultiplier` directly, so a carrier at 1.4 scales the whole chain. Note
   > also the rounding trap already logged for Building: sub-thousandth rates are rounded to
   > 3 decimals *after* the LCM multiply, so the multiplier changes which side of a rounding
   > boundary a rate lands on. LCM is not a clean post-hoc scalar.
2. ~~**Live RAaS envelope**~~ — **closed 2026-09-17.** A live request wraps the STC content
   in `header` + `body`, with `authorization.orgId` / `authorization.shipId` in the header.
   Confirmed against this account's real GL RAaS inputs. See §1.
3. **No execution.** `cf_engine/` still has no interpreter or rating kernel, so none of this
   has been run. It is a well-evidenced reading, not a tested contract.

4. **`OccupCategoryRiskSeverity` has no stated default.** Required by the Special Contents
   rate key, absent from all 364 ISO fixtures, constrained by no domain table. See §8.3 —
   this is the sharpest open question in the document.

Closed since the first draft: `ConstructionType`->`ConstructionCode` (Set 0),
`Group` A/B/C (Set 0), `ClassCodeToUse` (1a), `YARD` selection (1b),
STC validation across all 7 AL cases (1c), Basic Group II (1d),
STC corpus indexed and its coverage measured (2a-2c),
Personal Property `CovType` universe (3a), Broad and Special (3b),
second-state generalisation across the District states (3c).

---

## 11. Next steps

- **Use the STC corpus.** 924 payloads, 206 with Personal Property, 7 Alabama. These are
  ISO's own regression cases and should become the CF engine's test fixtures the moment
  there is an engine. They also answer format questions faster than the schema does.
- Trace `SetConstructionCode` and the `Group` resolution in
  `CommercialPropertyOccupClassRules.Rule.xml` / `CommercialPropertyStructureRules.Rule.xml`
  to close items 1 and 2.
- Diff the four AL STC editions (20221001 → 20230801 → 20240501 → 20250201) to see which
  payload fields ISO added over time — a cheap read on where the format is moving.
