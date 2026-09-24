# CF rater: RESUME HERE

**Updated 2026-09-23 (Group 1 closed).** Supersedes `CF_R8_HANDOFF.md`. Read this first, then the records it links.


> **2026-09-24:** RC-4 42-state re-run done. 40 of 40 rated states match Excel = ISO = engine on every line;
> CO / IN / OK / SC are ISO refusals (RC-3 inputs). Standard run 42 / 42 at 21171. Next: RC-4's remaining items.
>
> **2026-09-24 later: RC-4 DONE.** ED-CA-SC, ROOFRND, TH-DED, W-22, CA-D2, SC-GI-ST fixed / verified on live ISO (`124 --fix <ID>`,
> probes in `scenarios/rc4/`). Baseline 21171 unchanged. Committed 60d2267.
> **RC-2 DONE 2026-09-24** (W-3 W-4 W-5 S-2 ED-WHX FINRND; `scenarios/rc2/`). Committed 669b8bc.
> **RC-3 DONE 2026-09-24** (RC3GEO AZPFD S5 S4 + payload unit numbers; D-1c / D-2 no change). 44 / 44 states. Committed c4ce2de.
> **ED-FL DONE 2026-09-24** (FL V02 on disk; SCSTATE VACFL SUBSTD FLRES EDFLSTAMP; ENG-FL-MOD closed). Committed 8160b0b.
> **FL-BGII DONE 2026-09-24** (county / FL territory dropdowns). Committed 188e741. Specific/Tentative Group I verified built (Tentative payload fix). Committed e5be5dc.
> **Specific Group II DONE 2026-09-24** (BGIISPEC). Not committed yet. Committed 952b0a2.
> **Blanket Phase 1 DONE 2026-09-24** (Building Only, Average). Next: Blanket Phase 2 (Contents) -> 3 (BI) -> 4 (SC, Highest) -> Earthquake -> editions LAST.

---

## Where things stand

**Workbook:** `C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb` (the prototype). **Never touch 1.01.**
Risks are now entered on **`IN - Schedule`** (one row per record, 40 per block). The old
`IN - Location` / `IN - Special Class` sheets are **deleted** (R-8 Phase 5).

**Baseline premiums (read through the `OUT_Prem_*` names):**

| Building | Contents | BI | Special Class | SC BI | **Total** |
|---|---|---|---|---|---|
| 7597 | 8658 | 2964 | 1519 | 433 | **21171** |

(21160 before RC-1's NY Cyber correction, 21083 after the Cyber drop, 21016 after Group 1, 20970 at the start of 2026-09-23, 19994 the morning before. Every change was a fix verified against live ISO.)

**The main tool, a one-command Excel vs ISO vs engine comparison, per record per form:**

    python scripts/cf/119_payload_three_way.py

Excel must be closed. Results go to `results/cf-payload/<timestamp>/`. Cyber is dropped from the payload
automatically for states with no rows in `TBL - Cyber` (FL, NY), exactly as the rater drops it.

**Latest comparison (2026-09-23): 42 / 42 record-forms match Excel = ISO = engine (FL 15, NY 9, AK 9, CA 9);
total 21171 on all three sides.** No flags needed. Standing checks: this run + `136_column_consistency_audit.py --strict`.

---

## Done today (2026-09-22)

| Work | Record |
|---|---|
| R-8 Phases 2-6: Contents, Building, BI, Special Class and SC BI all read `IN - Schedule`, 40 records each; old input sheets retired; payload spec collapsed onto the Schedule | `CF_R8_Phase2b_Record.md`, `CF_R8_Phase4_Record.md`, `CF_R8_Phase5_Record.md`, `CF_R8_Phase6_Record.md` |
| Payload generator Steps 4-6: `Defaults` sheet, three-way CLI, first live runs | `CF_Payload_Step4-6_Record.md` |
| Rater fixes, each verified against ISO: Fix A/B (R-8 Gate 2), W-8 (SC own symbol), W-1, W-12 (open-sides symbol swap), W-13 (FL/WV roof factor), W-17 + W-6 (Contents Special), W-14 (BI Group II BCEG + rounding), W-10 / W-18 / W-19 (Special Class) | `CF_W11_Fixes_Record.md`; backlog `Rater_Simplifications_Backlog.md` |

Every fix script is under `scripts/cf/` (`109`-`120`). Backups before each step are in `Spreadsheet_Rater\CF\Backups\`.

---

## Done 2026-09-23: Group 1 (`CF_W16_W20_W21_Record.md`)

W-16 (BI Group I rounding + BI's own Cyber factor), W-20 (Legal Liability rate rounding), W-21 (round after each
Cyber factor: this was every $1 difference), and the payload now mirrors the rater's sprinkler-leakage assumption
on Contents / BI (S-4). Script `scripts/cf/124_w16_bi_fixes.py`.

## Next, in order

1. **Decided and built 2026-09-23:** FL/NY Cyber drop (`--fix CY`), Alaska rating-area inputs (`--fix AK`),
   NY County + NYC protection class (`--fix NY`). "Engine refuses NY" was DROPPED: ISO rates NY once the payload
   sends `CompletedBasicGroupIISymbol` = "Not Applicable". Record: `CF_W16_W20_W21_Record.md`.
   **RC-1 done 2026-09-23** (see `CF_Rater_Release_Plan.md`). ISO write-up drafted, FL only: `ISO_Filing_Gap_FL_Cyber.md` (user to send). **Next: RC-4's "more states" run, then RC-2.**
2. **Backlog still open:** W-4, W-5, W-7, W-22 (IRPM / mod rounding order, unverifiable while all are 1.0),
   S-4 / S-5 (missing per-group sprinkler and Cyber BI inputs), D-1c (NY territory factor), Special Class in NYC, dropdowns on blank Schedule rows, docs that still
   describe the old input sheets.

---

## How to work (what has held all session)

- **Hard rules:** never touch `CFRater1.01.xlsb`. Abort if Excel is running (a titled window means the user has
  it open, so stop and say so). DispatchEx only. Set `Calculation = manual` after open. Back up before every write.
- **Verify every fix against live ISO** with the three-way run, on **every** state ISO rates, not just the target
  (a BI fix that helped FL made AK worse, and only the all-state run caught it).
- **Gates:** active records must be unchanged except where the fix is meant to move them; inactive-slot
  differences are printed, never silently ignored. Structural changes are re-verified after save and reopen.
- **State tables:** resolve to each state's **latest** package across **all** edition folders
  (FL lives under the 2023 folders), and expand per state (no CW placeholder rows).
- **Premium-changing fixes are the user's call.** Trace, log to the backlog, ask, then apply.
