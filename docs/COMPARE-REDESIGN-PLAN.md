# Compare screen redesign: plan

Approved wireframe: `docs/compare-wireframe_20261016.html` (2026-10-16). Code: `ui/console_page.py`. Status: S1–S7 built 2026-10-16 (D1, D2 as recommended), plus a readability pass on every screen; committed 2026-10-27 (verify_console_upload 37/37, verify_console_deviations 89/89).

**In short:** first the console takes on Federato's colors and rounded corners, all screens at once, because they share one set of colors. Then the Compare screen gets the new layout. "Compare with ISO" moves into the Generate section and can always be clicked. Nothing about pricing or ISO calls changes.

## Steps

| # | Step | What changes | Size |
|---|---|---|---|
| S1 | Console colors and corners | Swap the shared `:root` colors in `PAGE` (line 876) to the Federato palette, keeping the token names so every screen follows. Replace the 28 hard-coded colors (`#fff`, `#2f72a8`, `#9a6214`, `#f8f4f4` on `.mx-side`, and others) with tokens. Raise the radii (2/4/7px to 6/10/16px), make `.btn` a pill, make status chips round. Add a teal primary button style. | M |
| S2 | Fonts | Point `--font-heading` and `--font-body` at Reckless and Case, falling back to Georgia and Arial. See decision D1. | S |
| S3 | Compare layout | Rewrite `UP_HTML` (line 1552) as three panels: 1 Generate a request, 2 Confirm before asking ISO, 3 How they compare. Upload and paste fold under the generator. Element ids stay the same so the JS keeps working. | M |
| S4 | Compare with ISO, always clickable | Add the button to the Generate panel and to the upload/paste fold. Remove `b.disabled` from `upDraw`. With nothing priced, a click generates the request, waits for our price, then opens the confirmation. With answers already stored, the confirmation names them and asks again, which replaces the `up-fresh` checkbox. | M |
| S5 | Plainer results table | Columns: Request, Our price, ISO's price, With company, Result, actions. Verdicts become "Same price", "Ours is 12.40 higher", "Waiting on you". "Trace Diff" becomes "Find where they split". Notes and ISO messages fold under the request name. | S |
| S5b | Side panel | "What the words mean" glossary, plus the existing upload summary counts. The deviation drill-down and the "why this value" panels stay as they are. | S |
| S6 | Tests | Update `tests/verify_console_upload.py` D1–D4 for the new ids and labels (`up-fresh` gone, a new id for the generator's Compare button). Add a check that the button is never disabled. Run the console tests. | S |
| S7 | Look in the browser | Run the app, open `/console#compare`, and check the three panels, the confirmation, and a mismatch row against the wireframe. Check the other screens still read well in the new colors. | S |

## Decisions for you

| # | Question | Recommendation |
|---|---|---|
| D1 | The console fetches nothing from outside (D7). Federato's fonts are not public. | Keep D7. Use Reckless and Case where installed, Georgia and Arial otherwise. Don't load Google stand-ins. |
| D2 | Restyle every screen in S1, or only Compare? | Every screen. They share one set of colors, so a Compare-only theme means a second copy. |
| D3 | Step 2 when nothing is waiting and nothing is stored | Not possible once S4 is in: a click always produces at least one request to confirm. |

## Not changing

- Pricing, the ISO call path (`upSend`, `/upload-send`), the ledger and the daily cap.
- The confirmation's over-cap reason box. It keeps the same rule and new styling.
- The worksheet, Trace Diff, and the deviation side panel. They only take on the new colors.

## Readability pass on every screen (added 2026-10-16)

- Body text 13px serif → 15px sans; every small size raised about 1.5px; table rows and side panels given more room.
- Table headers no longer in capitals; side-panel labels in sentence case.
- Pill tabs and buttons, round status chips, 6/10/16px corners; inputs 8px × 12px.
- Passed cells on the Readiness Matrix and Coverage Board use a soft teal so the dense grids stay calm.
- Compare: plain verdicts ("Same price", "Ours is 12.40 higher", "Not asked yet", "ISO would not price it"), a glossary in the side panel, specialist detail last.

## Coverage Board summary views (added 2026-10-16)

Wireframe: `docs/board-views-wireframe_20261016.html`. The board opens on **By way of pricing** (one line per path, its states as a bar, outliers named; Partly checked / Passed nearly everywhere / Not started), with **By state**, **Map** and the **Full grid** beside it; the choice is remembered per browser. A line opens its states as chips, a state opens every path in it, a tile opens the state; a chip opens the existing cell panel (scenarios, Find scenarios, send). `#board?state=XX` opens By state with that state open. Decision codes ("(D8: …)") are left out of names and kept in the hover text. Test: `tests/verify_console_upload.py` D8.

## Readiness Matrix summary views (added 2026-10-16)

Wireframe: `docs/matrix-views-wireframe_20261016.html`. The matrix opens on **By coverage** (one line per coverage, its states as a bar, outliers named), with **By state**, **What's left** (cards by next step with their ISO calls) and the **Full matrix** beside it; the choice is remembered per browser. A line opens its states, a state opens its coverages, a card lists its cells; a cell opens the existing panel (ways of pricing, open mismatches, sign-off, Open on the Coverage Board), whose back link returns to the level it came from. The agreement chart stays above the views. Test: `tests/verify_console_upload.py` D9.

## Test Plan Builder, risk first (added 2026-10-16)

Wireframe: `docs/plan-builder-wireframe_20261016.html`. Five steps (Start · Build the risk · What to vary · States · Review) in three columns: steps, the screen as a two-column form, and the live cost. General Liability's 38 fields sit on six submission-ordered screens; Property's on its catalog groups. Each field has a value (left on Standard, it keeps the base risk) and a Vary switch with ISO's values, the edges picked; "Rated in N of 51 states" comes from the board's controls. States are picked on a map with quick picks (all, regions, still to test, never rated for what is varied). Starts: build one risk, fill gaps, a preset, or a sweep. The Workbench's and the Matrix's links prefill the same screens.

Backend (`console/plans.py`): an optional `base` (fixed fields, merged into every scenario; a varied field wins), an optional `method` (`pairwise` default, `edges`, `all`), and `byState` / `notApplicableWhy` in the preview. A spec without them reads as before. Tests: `tests/verify_console_upload.py` D10, D11.

## Scenario Workbench, consolidated (added 2026-10-16)

Wireframe: `docs/workbench-wireframe_20261016.html`. The plan builder's submission screens on the left (each counts its changed fields), the form in the middle (changed fields highlighted, with Reset), and one live price card on the right: ours beside ISO's stored answer, then Ask ISO, Find where they split, Open the worksheet (in Compare), Plan tests from this risk, Save to the Regression Library. Every change reprices on our engine, free. "Which states can take it?" and "Price it in every state" are one "Across every state" panel: a map of our price, a table, and the response curve as its third tab. Property uses the catalog's form instead of raw JSON; the request stays editable under "Edit the request directly". Mode and rounding sit under "Engine settings".

Backend: `console/workbench.build` builds a Property risk from form fields; `every_state` takes a line, and the `every` route prices Property in every state. Tests: `tests/verify_console_upload.py` D12, D13.

## Carrier Filings, high level and Test it (added 2026-10-16)

Wireframe: `docs/filings-wireframe_20261016.html`. A summary strip (filings, companies and states, the range of effects against ISO, how many are tested), then three views: **Filings** (one card per filing with each company's effect, its progress and when it was last tested), **Companies** (each company against each line and state, shaded by its effect; "ISO's rates" where it has no filing) and **Timeline** (effective dates for new and renewal business). A filing opens below in five tabs: In short, What changes (companies side by side, the version in use; every version in full folded below), Effect on premium (bars by type of business in the filing's own state), **Test it**, and Paper trail (proving suite, quick checks, our review, history, documents). Uploading moves to a drop zone in the side panel.

**Test it** is a streamlined check, not the full ISO sweep (`console/filing_tests.py`):
- *The filed factors apply as written*: typical businesses priced technical and carrier; each filed row's coverage premium against technical must match the filed factor, within 1% (General Liability) or 2.5% (Property, whose coverages carry parts priced at another group's factor or none). Minimum premiums are checked on every risk; parts the typical set never reaches are listed.
- *The effect is what we expect*: the same risks against the impact recorded when the filing went into use, scaled to the whole typical set, within ±1 point. Expected defaults to the recorded effect; a typed figure replaces it (`results/deviations/filing_tests/expected.json`). The insurer's own filed figure, where a filing gives one (`carrier_expected` in its `source.json`), is shown as a sense check.
- *ISO agrees* (optional, behind a confirmation): D21, ISO only ever prices technical. One typical business per state is sent as its plain ISO request and ISO's premium must equal our technical; a request ISO already answered costs nothing. (The wireframe first drew this as sending the filed factors to ISO; corrected before the build.)
- *Try one*: any business just priced, both ways.

Quick (one risk per class, medium size) takes about 20 seconds for General Liability and 2 minutes for Property; the whole typical set is an option. One test runs at a time; "Run the quick checks on every filing" queues them. First run, 2026-10-16: all three UFG filings pass both checks; every company's effect matches its recorded figure exactly. The Effect tab now uses each state's own figures (United Fire's property impact covers Alabama and Iowa together). Tests: `tests/verify_console_deviations.py` K1–K8.
