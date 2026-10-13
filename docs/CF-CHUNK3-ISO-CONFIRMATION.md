# Property chunk 3, task 8 — ISO confirmation of the sweep

Run 2026-09-18, `scripts/cf/19_chunk3_raas_sweep.py`. **7 calls, 7 matches.**

| Case | Predicted | Engine | **ISO** | Messages (engine / ISO) |
|---|---|---|---|---|
| OR Broad — control | 16 | 16 | **16.00** | 2 / 2 |
| OR Special — control | 54 | 54 | **54.00** | 3 / 3 |
| FL Broad | 16 | 16 | **16.00** | 1 / 1 |
| **FL Special** | **38** | 38 | **38.00** | 2 / 2 |
| NY Special | 58 | 58 | **58.00** | 3 / 3 |
| AL Special | 46 | 46 | **46.00** | 3 / 3 |
| OR Special + theft (CP 10 33) | 47 | 47 | **47.00** | 2 / 2 |

Five jurisdictions, each chosen because it tests a different structural claim —
not 47, because a call per state would only re-confirm arithmetic the offline
sweep already derives from the same filed rows.

Every premium was hand-derived, then checked against the engine, and only then
sent. The engine agreed with all seven predictions before a single call was
made, so an ISO disagreement would have been attributable to the reading rather
than to the arithmetic.

---

## What each call actually settled

**FL Special at $38 — the call that mattered.** `SpecialBuildingRate` finds no
Florida row, so a table-name reading says Florida cannot rate Special at all —
which is what the sweep's first pass concluded. The claim that Florida rates
through its own overriding rule, reading
`SpecialBuildingRateNonResidential`, chosen on a hardcoded list of 21 class
codes, was **ours alone until this call**. ISO returns 38.00. The reading holds.

**NY Special at $58** confirms the key choice every prediction in the sweep
depends on: New York files no `DeductibleFactor` of its own, so the countrywide
0.92 applies where Oregon's own filing gives 0.97. If "does this state file
this table?" were being read wrongly, NY is where it would show.

**AL Special at $46** confirms that an override is not automatically a
divergence. Alabama overrides `SetSpecialBaseRate`, `SetSpecialRate` and
`SetBroadRate` and still lands exactly on a countrywide-shaped prediction.

**OR Special + theft at $47** confirms task 18 externally: an endorsement
record attached to the **structure** reaches ISO's premium the same way it
reaches ours, and the 0.88 credit is real.

---

## The message counts matched exactly, in all seven

Two / three / one / two / three / three / two — engine and ISO, case for case.
That is not something any of these runs was designed to test, and it is the
strongest evidence so far for gate point 9, which is still owed on chunks 1
and 2. Our message set is not merely *similar* to ISO's on these payloads; it
is the same size on every one.

Two observations worth keeping:

**Attaching the theft exclusion silences a validation message.** Oregon Special
returns three messages, one of them *"Select a valid Theft Deductible with
Theft Coverage included"*. With CP 10 33 attached the premium drops to $47 and
that message is gone — two remain. The endorsement changes the *validation*
outcome as well as the rate, which is exactly the mirrored-pair behaviour the
gate's own note warns about: attaching an endorsement to silence one message
can raise its opposite.

**Florida files its own form number for the same rule.** Countrywide returns
*"CP 03 20 Must Be Attached…"*; Florida returns *"CP 03 22…"*. Same check, same
condition, a different form cited — so a message register keyed on form number
rather than on rule name would split one entry into two.

---

## Puerto Rico cannot be confirmed, and that is the finding

PR is excluded from this run and from every future one: the RAaS subscription
does not cover it (`NO_ISO` in `scripts/raas.py`, closed as OI-86 on
2026-08-13).

PR is also the jurisdiction with the most unusual Special reading in the whole
corpus — its own cause-of-loss domain (`Special Including Theft` /
`Special Excluding Theft`, values that exist nowhere countrywide), its own
construction-keyed rate table, its own theft-exclusion rule, its own Broad base
rate and its own LOI table.

**So the one jurisdiction that most needs external confirmation is the one that
can never have it.** Every PR premium this engine produces rests on a reading of
the filed rules and nothing else. That has to be stated wherever a PR premium is
presented, not left for a reader to discover.

---

## Running total

**~27 ISO calls across the project, and the engine has matched every one.**
