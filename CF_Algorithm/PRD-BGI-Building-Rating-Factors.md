# PRD — CF Basic Group I Building: Reference Workbooks → Excel Rater

**Status:** draft, 2026-09-04. **Owner:** this project (`CF_Algorithm`), consumed by
`Spreadsheet_Rater\CF`. **No build authorized yet** — this PRD scopes what wiring these factors into
`CFRater1.01.xlsb` would require; it does not itself authorize doing so.

---

## 1. Problem

`CFRater1.01.xlsb` (the Excel rater) needs to compute a Basic Group I (BGI) Building premium. Getting
there requires roughly a dozen distinct rating factors, each with its own lookup mechanism, each of
which varies by state in a different way (some are flat CW constants, some vary in a handful of
states, one or two vary in almost every state). Before any of this gets wired into the live rater, each
factor needed to be reverse-engineered from the ISO ERC filing (the machine-readable source of truth)
and cross-checked against the ISO Commercial Lines Manual, then turned into something an underwriter or
a spreadsheet formula could actually consume.

## 2. Scope

**In scope for this PRD:** the BGI Building rate build-up, factor by factor, as documented in
`BasicGroupI_ERC_Tables.md` and `CauseOfLoss_Building_RatingAlgorithms.md`.

**Out of scope:** Personal Property, Business Income, Special Class, and every other CF coverage form
(each has its own separate ERC datadef group and its own naming — see
`project_cf-bgi-sprinkler-leakage-exclusion` memory for a concrete example of why these can't be
assumed to share a mechanism with Building even when the factor name looks identical). Also out of
scope: wiring anything into `CFRater1.01.xlsb` itself, beyond the one narrow exception in §5.

## 3. What's been built

Nine standalone Excel workbooks, all in `Spreadsheet_Rater\CF\Supporting Tables\`, each independently
verified against the ERC source (all 47 filed states checked, not sampled) and, where precision
mattered, against the CW manual text. None of these are wired into the live rater.

| Factor | Workbook | Mechanism | State variation |
|---|---|---|---|
| Territory Factor | `BGI_Territory_Lookups.xlsx` | Direct-select dropdown, sourced from the filed factor list | 3-tier: fixed (19 states, factor always 1), City-only dropdown (21), City+County composite (7 — FL GA KY MD NY PA VA) |
| AK/CA/NY Base Rate split | `BGI_LossCost_Tables_AK_CA_NY.xlsx` + `AK_District_ZIP_Mapping.xlsx` | Two full rate tables (District I / District II), gated by a state-specific input | Only these 3 states split; AK's ZIP-to-District map is **constructed, not ISO-filed** — see §6 |
| Protection Class | `BGI_ProtectionClass_Tables.xlsx` | ProtectionClass × ConstructionCode lookup | CW 28-code scale everywhere except North Carolina, which files its own 12-code scale |
| Roof Surfacing ACV / Cosmetic Exclusion | *(planning only, no workbook)* | Rule 74.A.3.b/c — ACV factor + separate cosmetic-exclusion factor | CT/MA/NH file an override row the countrywide branch logic can never reach |
| Sprinkler Leakage Exclusion | `BGI_SprinklerLeakageExclSprinkleredFactor.xlsx` | Credit subtracted from the fully-loaded rate (after Territory/Protection/Roof), not baked into the base rate | Only live for Specific/Tentative rating; sprinklered/non-sprinklered terms mutually exclusive |
| Coinsurance Factor | `BGI_CoinsuranceFactor.xlsx` | 4-branch: bypass (Builders Risk / Functional Valuation), standard 80/90/100%, blanket (same table), flat 1.5 sub-80% surcharge | FL files an unreachable 70% row |
| Limit of Insurance (LOI) Factor | `BGI_LOIFactor_Building.xlsx` | Native linear interpolation via the rate table's own `InterpolateMode="Linear"` metadata | PR files a fully distinct 342-row curve |
| Deductible By Location Factor | *(planning only, no workbook — trivial)* | Flat 0.995 when CP 03 29 is scheduled, stacks multiplicatively with Deductible Factor | Universal, no state variation found |
| Deductible Factor | `BGI_DeductibleFactor.xlsx` | Dropdown of available deductible amounts + amount-keyed factor table | 7 distinct shapes: CA/FL/NY/PR capped at $75K (10 options); 39-state "Common" table + NV/PA/TX/UT variants up to $1M (16 options), NV/TX/UT coarser-grained bands (same coverage, fewer breakpoints) |

Each workbook follows the same convention: a **Read Me** sheet documenting source/method/caveats, a
**Walkthrough** sheet with live, cell-anchored formulas (no hardcoded results), and the underlying
table(s) themselves.

## 4. What's confirmed vs. still open

**Confirmed this session** (previously wrong or unverified, now settled):
- The ERC engine interpolates LOI natively via table-definition metadata — not a manual-only step, as
  first assumed.
- Sprinkler credit applies after the full multiplier chain, not baked into the base rate.
- Deductible Factor's dropdown and table both vary genuinely by state (not just the table).
- NV/TX/UT/PR's Deductible Factor row counts are coarser filing granularity, not incomplete data.
- CA's Deductible Factor has no state override at all (an earlier pull used a future, not-yet-in-force
  edition and wrongly showed CA offering options up to $1M).

**Still open / not yet reviewed:** every BGI Building factor not listed in §3's table — this PRD covers
what's been worked so far in this factor-by-factor pass, not the complete rate build-up. See
`BasicGroupI_ERC_Tables.md` for the full table inventory and which rows still lack a "session findings"
pointer.

## 5. Production rater changes made to date

**One, by explicit narrow request:** a `BGI Territory Factor` tab (named cells only, no formulas or
other functionality) was added to `CFRater1.01.xlsb` via PowerShell/COM automation (openpyxl cannot
write `.xlsb`). A pre-change backup exists at `Backups\CFRater1.01_backup_pre-BGITerritoryFactor.xlsb`.

Nothing else has been wired in. Per this project's standing rule, no further building into the live
rater happens without an explicit go from the user, factor by factor.

## 6. Known gaps — flag, don't hide

Per standing instruction, every shortcut below must be treated as a gap to close before production
use, never presented as compliant:

- **`AK_District_ZIP_Mapping.xlsx` is constructed, not ISO-filed.** Built from Alaska Rule 70's legal
  district boundary description (First Judicial District, east of the 141st Meridian), not from any
  filed ZIP-level table — none exists. If AK BGI rating is ever wired into the live rater, this mapping
  needs underwriting sign-off or a better source before being trusted at the ZIP level.
- **Deductible Factor's NV/PA/TX/UT variants** file fewer intermediate limit breakpoints than the
  39-state Common table. Confirmed this is intentional filing granularity (full limit range is still
  covered), but worth re-verifying if a future edition pull for those states looks unexpectedly short.
- **State edition selection is a recurring trap.** Two separate incidents this project (CA's
  DeductibleFactor this session, an earlier one flagged previously) came from pulling a future,
  not-yet-in-force edition instead of the state's actual authoritative edition per
  `State_ERC_CW_Editions.csv`. Any future factor pull should check that file first, not glob a
  directory and take the newest-looking folder.

## 7. Next steps

1. Continue the factor-by-factor pass through the remaining BGI Building rate build-up (next factor
   not yet chosen).
2. Once a meaningful set of factors is reviewed and stable, get an explicit go to wire one or more
   Supporting Tables workbooks into `CFRater1.01.xlsb` itself — this has not happened yet beyond the
   single Territory Factor tab.
3. Resolve the AK ZIP-mapping gap (§6) before AK BGI rating goes anywhere near production use.
4. Keep `BasicGroupI_ERC_Tables.md`'s "session findings" annotations current as each new factor is
   reviewed, so this PRD's §3 table stays a pointer, not a duplicate source of truth.
