# ISO ERC question: Florida Cyber Incident Exclusion factors (Commercial Property)

**Draft for the user to send. Prepared 2026-09-23. Nothing has been sent.**

---

**Subject:** CF Florida: Cyber Incident Exclusion requests fail with "No results have been returned"

Hello,

When a Florida Commercial Property request includes either Cyber Incident Exclusion endorsement record, the Rate
service returns HTTP 400 instead of a premium. The same request without the Cyber records rates normally.

**What we see**

| Record sent | Error (abridged) | RequestId |
|---|---|---|
| `CommercialPropertyCyberIncidentExclusion` | Lookup Rule at line 7452 in `CommercialPropertyRules` (Project CF CW 20230801 V04): Matrix `CyberIncidentExclusionFactors`, Project **CF FL 20241201 V02**, Keys: CW, Basic Group I. No results have been returned. | 4badc19e-dfe2-4841-bdb6-021c3dcfbbca |
| `CommercialPropertyCyberIncidentExclusionWithEnsuingCausesOfLossExceptions` (property-damage and aggregate LOI 500,000) | Lookup Rule at line 7473: Matrix `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors`, Project CF FL 20241201 V02, Keys: CW, Basic Group I, Sublimit, Yes. No results have been returned. | 118bc02f-229e-4795-b52f-6c02f8c5e217 |

**What we found in the ERC content**

- Every Florida package we hold (CF FL 20201201 V01, 20220701 V01, 20231101 V01, 20240301 V01, 20241201 V01) files
  both `CyberIncidentExclusionFactors` and `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors`
  **header-only**, with no rows. Because the state table replaces the countrywide one, the countrywide fallback
  lookup (`CW` key) also finds nothing.
- Florida does not override the countrywide `SetCyberIncidentExclusionFactor*` rules, so they still perform the
  lookup and fail.
- New York also files both tables header-only, but its package **overrides** those rules (exclusion factor 1.0;
  exceptions factor from its own `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactorNY`, 1.005). New York
  rates successfully with the same records.

**Our questions**

1. Is the Cyber Incident Exclusion (CP 10 75 / CP 10 76) meant to be **unavailable** in Florida? If so, could the
   service return a validation message saying so, rather than a lookup failure?
2. If it is available, what factors apply in Florida? Are the empty tables in CF FL 20241201 an omission?

Thank you.

---

*Internal notes (remove before sending):* evidence runs are under `results/cf-payload/20260923-085749` (the Florida
request, re-sent with each Cyber record). Until ISO answers, the rater applies no Cyber factor in Florida (`TBL -
Cyber` has no FL rows) and the payload omits the Cyber records for Florida. The earlier draft's New York claims
(Cyber, and the "empty construction-symbol table") were both wrong and are not in this note. Live ISO runs **CF FL
20241201 V02**; only V01 is on disk here, so the local Florida snapshot is behind.
