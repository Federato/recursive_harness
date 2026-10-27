# Question for ISO: Florida's SPP special-class condo endorsement never attaches (OI-116)

**Status: written 2026-10-05 (chunk 28 C28-14), not yet sent.** Our engine keeps the record and prices it until ISO
answers (pinned as a known difference in `scripts/cf/208_chunk21_rc2.py`, FC5).

## The question

On a Florida **Standard Property Policy**, a special class item on the Condominium Commercial Unit Owners form with
`ItemsBelongToResidentialCondo` = "Yes" should, as we read FL 20241201 V02's
`CommercialPropertySpecialClassRules.AttachFormChangesCommercialUnitsInResidentialCondosIncludingOptionForAddlCoveredPropertySPPSpecClass`,
carry the record
`CommercialPropertyChangesCommercialUnitsInResidentialCondosIncludingOptionForAddlCoveredPropertySPPSpecClass`
(the SPP special-class version of the commercial units in residential condominiums change). RaaS never returns it:
sent, it is removed; not sent, it is not created. **Which of the rule's three conditions does RaaS read as false here,
and why?**

The rule's test, as filed (all three must hold; otherwise it removes the record):

1. `CovForm` = "Condominium Commercial Unit Owners Coverage" (on the special class)
2. `../../../../PolicyType` = "Standard Property Policy" (the policy)
3. `ItemsBelongToResidentialCondo` = "Yes" (on the special class)

## What we sent, and what came back (RaaS, effective 2026-09-17, scheme CF FL 20241201 V02)

Policy: FL, `PolicyType` "Standard Property Policy". Special class: "Cooling Towers - Metal", Building, Special, limit
100,000, `CovForm` "Condominium Commercial Unit Owners Coverage", `ItemsBelongToResidentialCondo` "Yes".

| Request (saved in `results/cf-raas/`) | Variation | The SPP special-class record in the response | Policy total |
|---|---|---|---|
| `chunk21_rc2_FC5` | the record sent, manual premium 300 | **absent** (removed) | 1,400 (ours 1,693: the record's $293) |
| `chunk21_rc2_FC5auto` | the record not sent, for RaaS to auto-attach ("Yes"; also tried "Y", "YES") | **absent** (not created) | 1,400 |
| `chunk27_oi116_as_sent` | FC5 re-sent unchanged | **absent** | 1,400 |
| `chunk27_oi116_SC_PolicyType_removed` | the special class's own `PolicyType` field removed | **absent** | 1,400 |
| `chunk27_oi116_SC_PolicyType_SPP` | the special class's `PolicyType` set to "Standard Property Policy" | **absent** | 1,400 |

## What we have ruled out

* **Conditions 1 and 2 work elsewhere:** the sibling records agree with RaaS: the CPP special-class version (FC3) and
  the SPP occupancy version (FC4) attach as the rules say, reading the same `CovForm` and the same `PolicyType` path.
* **Condition 3's field is declared and allowed:** `ItemsBelongToResidentialCondo` is on
  `CommercialPropertySpecialClass` in every countrywide schema (string, length 3); FL's form field takes the YesNo
  domain and shows it when `CovForm` is a condo form, which FC5's is. No FL or countrywide rule writes or clears it.
  RaaS does not echo it in the response (nor several other special class inputs), so the echo cannot show what it read.
* **Not the special class's own `PolicyType`:** removed, or set to "Standard Property Policy": still absent.
* **No ISO test fixture covers it:** all 364 Commercial Property payloads in the STC corpus are Commercial Property
  Policies; none is an SPP.

## Why it matters

The record carries a manual premium: on FC5, ours prices $293 that RaaS does not, and the policy totals differ (1,693
against 1,400). It is the one premium difference with RaaS that the open-items register still holds open and
unexplained for Property.
