# R-6 implemented — the edition and state basis is now on the face

**2026-09-22.** Applied to `CFRater1.02.xlsb`. `CFRater1.01.xlsb` never opened.
Premiums unchanged — additive only.

| | |
|---|---|
| Source stamps | **19**, one per `TBL -` sheet, 0 duplicates |
| New sheet | **`TBL - Editions`** — 52 rows (47 filed + 5 with no filing) |
| New section | **`OUT - Diagnostics` §5** — live, one row per location slot |
| Sheets now | 28 |

---

## What it says on the current sample

| Loc | State | ERC edition | Age | Flags |
|---|---|---|---|---|
| 1 | FL | CF FL 20241201 V01 | **21 mo** | **STALE — 21 months.** Not in the current snapshot batch. Own Residential/Non-Residential BGII rule. Files 11 `SpecialClassDescription` strings absent from CW |
| 2 | NY | CF NY 20260801 V01 | 1 mo | District split (NYC). Special Class BGI deviates from CW on 84 values, swings over 400% |
| 3 | AK | CF AK 20260601 V01 | 3 mo | District split. ZIP mapping is a known-inaccurate shortcut (D-1) |
| 4 | CA | CF CA 20251201 V01 | 9 mo | District split, user-picked District field |

Age is computed against `TODAY()`, so the staleness warning maintains itself rather
than needing a person to notice a date drifting.

---

## The design decision that matters — the stamp lives on the data

The obvious build is a central table of "which edition each sheet came from". **I
argued against that and built it differently**, because a table *about* the data
drifts from the data: someone refreshes rates for a new ISO filing, forgets the
central ledger, and the workbook then confidently reports a stale edition for current
rates — which is worse than saying nothing.

That is the same failure this entire session has been about, twice over: a
build-status page 11 days behind the workbook, and a payload spec two chunks behind
the repo.

**So each `TBL -` sheet carries its own stamp**, in the far-right columns:

```
-- SOURCE STAMP --
Holds             Building Basic Group I rates
Varies by state   Yes
Source            per-state ERC
Edition basis     see TBL - Editions
Pull date         not recorded
Stamped           2026-09-22
On refresh        update the rows AND this stamp in the same edit
```

Refreshing the data and refreshing its provenance are now the **same edit**, in the
same place. They cannot drift apart.

**Written into columns, never inserted as rows.** Inserting a row at the top of a
table sheet would shift every absolute reference pointing into it. The stamp sits two
columns clear of the data instead.

**"Pull date: not recorded" is deliberate.** Most of these sheets genuinely have no
recorded provenance. Writing the truth makes the refresh checklist honest; inventing a
date would have made the stamp worse than useless.

---

## An absent state is a row, not a gap

`TBL - Editions` carries explicit **NO FILING** rows for HI, ID, LA, MS and WA:

> *No CF filing in ANY of the eight snapshot batches. Cannot be rated from this corpus.*

A lookup that silently misses is precisely how a state prices at zero unnoticed — the
same failure mode as the eight absent-means-zero input cases. The `VLOOKUP` in §5
returns `CANNOT RATE — no filing`, and a state not in the ledger at all returns
`STATE NOT IN LEDGER` rather than an empty cell.

---

## Two bugs found in my own work, both from re-running

**Dates.** Excel silently coerced the ISO date strings to serials on write, so
`DATEVALUE` on them errored and the Age column came back blank — the headline number
missing. Fixed with an `ISNUMBER` branch that handles either form.

**Duplicate stamps.** The stamp column was computed from `UsedRange`, but the previous
stamp *is* part of the used range, so a second run wrote a fresh stamp two columns
further right. Re-running left **36 stamps across 18 sheets.** The script now clears
every existing stamp before placing one, so it is genuinely idempotent — verified at
19 stamps, 0 duplicates.

Worth naming: both bugs only appeared on the **second** run. A script that is correct
once and wrong when repeated is a real hazard for anything meant to be re-run at each
edition change, which this is.

---

## Honest limits

- **It reports; it does not enforce.** It will tell you Florida is 21 months stale. It
  will not stop you quoting Florida, and it cannot tell you whether the newer filing
  would change the number — that needs the newer package pulled and compared.
- **A state with no filing still needs your decision** — refuse, or quote with a loud
  caveat. §5 surfaces the question; it does not answer it.
- **The flags are only what this project has established.** An empty flag means
  "nothing known", not "nothing to know".
- **The stamps record what is known today.** Eighteen of nineteen say
  `Pull date: not recorded`, and that will stay true until someone refreshes a table
  and fills it in.

---

## Scripts

`scripts/cf/100_r6_edition_basis.py` — idempotent: rebuilds `TBL - Editions`, clears
and re-places every stamp. Run `99_r7_diagnostics_tab.py` first if §5 needs rebuilding,
since that script recreates the diagnostics sheet.

---

## Streamlining status

| | |
|---|---|
| **R-1** · **R-2** · **R-3** · **R-4** · **R-6** · **R-7** | done |
| **M-1** Special Class factors · **T-1** total premium | fixed along the way |
| **R-5** split exclusion inputs per datadef group · **R-8** row-per-item inputs | remaining |

**R-8** is the one that matters more: it removes the 10 locations × 1 building × 1
occupancy class ceiling, and it overlaps the payload generator's `Payload Export`
sheet — doing R-8 first would shrink that sheet to mostly direct references instead of
a transposition layer built and then thrown away.
