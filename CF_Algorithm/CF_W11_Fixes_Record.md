# W-11 traced and fixed: open-sides symbol, Florida roof factor, Legal Liability AII

**2026-09-22.** `CFRater1.02.xlsb`. Script: `scripts/cf/120_w11_fixes.py --fix W1 | W13 | W12`.
Backup: `Backups/CFRater1.02_pre-W11fixes_*.xlsb`. **Every fix was verified against live ISO** by
re-running `scripts/cf/119_payload_three_way.py --without-cyber FL`, not against ourselves.

**Premiums: 7183 / 8022 / 2699 / 1633 / 457 / 19994 → 7525 / 8254 / 2996 / 1633 / 457 / 20865.**
Only item 1 moved (FL: Legal Liability, open sides, Specific, roof limitation A and B). Each fix's gate
held every other active record to "unchanged".

---

## In plain English

The Florida building was under-priced against ISO on its Group II and contents lines. The first guess
(the Legal Liability shortcut) was wrong: the rater already takes it the way ISO does. Tracing it
turned up three separate rater gaps, each now fixed and each confirmed by ISO moving onto the rater's
number:

1. **Open-sided buildings use a different Group II symbol** (W-12). ISO swaps the building's
   construction symbol before it looks up the Group II rate, for open-sided buildings and a handful
   of classes. The rater didn't. For this building that meant AB where ISO uses B, a base rate of 0.088
   where ISO's is 0.129.
2. **Florida (and West Virginia) have no roof-surfacing factor** (W-13). Both file ISO's table empty.
   The rater applied the countrywide 0.98 everywhere.
3. **Legal Liability contents skipped the Additional Insurable Interest factor on Broad/Special** (W-1).

## What changed

| Fix | Rater change |
|---|---|
| W-1 | Contents rows 76 / 104 test the coverage form, like row 53 (80 cells) |
| W-13 | New **`TBL - RoofSurfacing`**, 122 rows, per state, **no rows for FL and WV** (ISO header-only in every edition). Bldg Rating rows 9 / 40 look it up per state and fall back to 1.0 |
| W-12 | New **`TBL - BGIISymbolToUse`**: AdditionalClasses 1,626 rows, RoofConstruction 366, OilStations 46, superior-roofing list. Per state, from each state's **latest** package (FL, GA, KS, MT file their own). New **CoreScratchpad row 287 `BGIISymbolToUse`** = ISO's `SetBGIISymbolToUse`, with Montana's own variant. It now feeds the Group II base rate (59), lowest base rate (72) and wind/hail exclusion (205 and Contents' copy, row 166) |

**NY and PR file all three symbol tables header-only.** ISO itself can't rate them (the same pattern
behind New York's refusal). The rater gives them countrywide rows, and the table's source note says so.

## Verified against ISO (FL item 1, Excel → ISO)

| | before | after | ISO | left |
|---|---|---|---|---|
| Building BGI | 511 | 521 | 527 | -6 ≈ Cyber |
| Building BGII | 651 | 983 | 999 | -16 ≈ Cyber |
| Contents BGII | 885 | 1069 | 1082 | -13 ≈ Cyber |
| Contents Special | 191 | 239 | 340 | **-101 → W-15** |
| BI BGII | 640 | 937 | 862 | **+75 → W-14** |

"≈ Cyber": the rater applies the Cyber Incident Exclusion (×0.995 ×0.997); ISO's Florida filing has no
factor for it, so the comparison runs with Cyber dropped (`--without-cyber FL`).

## Two process lessons, stated as missing checks

- **Step 3's defaults and "omit v1" list were written without a live ISO run, and three were wrong**
  (Group II basis, the contents specific rate, roof surfacing). The missing check is exactly the three-way
  run: any payload default should be justified by ISO moving onto the rater's number, not by reading.
- **The fix script first searched one edition folder for state overrides**, which would have handed
  Florida the countrywide roof factor it was written to remove. The missing check: resolve every state
  table to the state's latest package across all editions, and print which package each state resolved to.

---

## Follow-on: Contents Special (W-17, W-6, W-15), 2026-09-22

| Fix | Change | Verified against ISO |
|---|---|---|
| **W-17** | Contents row 88 RATE = `ROUND(base x LCM x PrsnlPropTerrMultiplier, 3)`; the multiplier (row 87) was computed and never applied | FL LL item 239 → 335 (ISO 340); this was all of **W-15** |
| **W-6** | Contents row 97 = `INDEX('CALC - Bldg Rating'!$C$100:$AP$100, 1, ParentCol)`, the building's Special deductible factor (ISO ancestor copy), not the contents-limit band | CA 1086 → **992 = ISO**; AK 492 → **477 = ISO** |

**Premiums now 7525 / 8596 / 2996 / 1633 / 457 = 21207.** Backup: `Backups/CFRater1.02_pre-W17-W6_*.xlsb`.
The gate script also gained a retry for Excel's "call rejected by callee"; the first W-6 attempt stopped
on it without saving.

**Not covered:** the old contents deductible chain handled a *theft* deductible that differs from the main
one (CoreScratchpad 176-182 copies). Following ISO's ancestor copy drops that branch for contents Special. No
risk in the workbook exercises it, so it's unverified either way.

---

## Follow-on: BI Group II (W-14), 2026-09-22

BI row 33 RATE now = `ROUND(ROUND(base x LCM x numeric x adj, 3) x building BCEG, 3)`. The BCEG factor was
missing entirely. The W-12 base-rate fix is what made the gap visible. The first version (BCEG inside a single
ROUND) fixed Florida but made Alaska worse (78 → 70 vs ISO 79). That exposed ISO's rounding order, which the
second pass (W14R) applies. **Verified:** FL 855 (ISO 862, -7 = Cyber), AK 78 (79), CA 15 (15).
**Premiums 7525 / 8596 / 2914 / 1633 / 457 = 21125.** Backup: `Backups/CFRater1.02_pre-W14_*.xlsb`.

**Lesson, stated as the check:** a fix verified on one state can be wrong in another. Always re-run the
three-way comparison on **every** state ISO rates, not just the one the fix was aimed at. That is how the
Alaska regression surfaced within minutes.

---

## Follow-on: Special Class (W-10, W-18, W-19), 2026-09-22

**Payload first.** ISO's Special Class `ClassCode` is an input (its vandalism rule gates on it), and
deductible-by-location is an endorsement record. Neither was sent. Once they were, ISO's FL Special Class
Group I moved 821 → 744, and the three rater gaps became visible.

| Fix | Rater change | Verified (FL, Excel → ISO) |
|---|---|---|
| **W-10** | Rate key (row 172) uses the **location's** protection class; ISO `ProtectionClassToUse` | SC BGI 875 → 774 · SC BI BGI 216 → 188 (190) |
| **W-18** | Row 221 `VandalismExclRate` from the rater's own rate table; subtracted from the Group I rate where filed (FL only), factor neutralised | SC BGI 774 → 733 |
| **W-19** | `TBL - DeductibleByLocation`, per state, **FL has none** (header-only); replaces the literal 0.995 in Bldg 19 / 49 and SC 12 / 36 | SC BGI 733 → **738** (744) · BGII 626 (631) · Special 142 (144) |

**Premiums 7525 / 8596 / 2914 / 1506 / 429 = 20970.** Backup: `Backups/CFRater1.02_pre-SCfixes_*.xlsb`.
FL-specific mechanisms are data-driven: they switch on because a state files the table, not because the
state is "FL". Today FL is the only state that does.
