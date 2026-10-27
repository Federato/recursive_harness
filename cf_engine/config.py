"""Where the Property corpus lives, and the date below which it is refused.

Settable by environment variable so the engine is not welded to one machine,
with a working default because every Property analysis script in this project
already assumes it.
"""
from __future__ import annotations

import os
from pathlib import Path

#: Root of the ISO ERC Commercial Property corpus.
CORPUS_ROOT = Path(os.environ.get(
    "CF_ERC_ROOT", r"F:\ISO_ERC_Files\CF"))

#: Directories under the root that are not edition batches.
EXCLUDE_DIRS = frozenset({".claude"})

#: The jurisdiction token the countrywide layer uses in its own namespace.
COUNTRYWIDE = "CW"

#: Below this date the corpus holds no Property package at all -- its earliest
#: edition is 20191201.
#:
#: **This is a floor on existence, not on coverage**, and the difference
#: matters. General Liability's floor (`gl_engine.config.MIN_ASOF`) is a
#: coverage floor: below it the corpus cannot resolve all 51 jurisdictions, so
#: a date under it would be served partially rather than refused. No equivalent
#: measurement has been made for Property. Until it has, this refuses only what
#: is certainly unanswerable and does not pretend to guarantee completeness
#: above it -- `scripts/cf/00_chunk0_checks.py --coverage` reports what actually
#: resolves at a given date.
MIN_ASOF = "20191201"

#: The rounding mode every Property rating uses. **PROVEN 2026-09-17, against
#: ISO's own service. No longer an assumption.**
#:
#: ISO declares `DecimalPlaces` on every rounding operator and never declares a
#: MODE, anywhere in either corpus. Half-up, half-even and truncate differ on
#: exactly the half-cent a rating engine meets constantly, so the engine cannot
#: avoid choosing -- it can only choose visibly. Half-up was directed as the
#: working assumption; it has now been demonstrated.
#:
#: **Why every earlier result was silent on this.** Nine Property cases, 47
#: jurisdictions and Oregon against ISO's service all matched to the penny --
#: and every one of them is consistent with ALL THREE modes, because not one
#: lands on a tie. A matching premium says nothing about rounding unless the
#: case was built to produce one. So two were built
#: (`scripts/cf/07_rounding_tie.py`), searching 58,656 combinations of class,
#: limit and deductible in Oregon for cases where the modes disagree:
#:
#:   ties at the PREMIUM (0 dp)   class 0074, limit 50,000, ded 500
#:       half-up $39   half-even $38   truncate $37   ISO: **$39**
#:   ties at a RATE step (3 dp)   class 0582, limit 52,500, ded 1,000
#:       half-up $65   half-even $64   truncate $64   ISO: **$65**
#:
#: Two scales were tested deliberately: the chain rounds to 3 decimals at every
#: `rul:Product` in the rate build-up and to 0 at the premium, and a case that
#: ties at one scale says nothing about the other. Both answer half-up.
#:
#: **Scope, stated rather than assumed.** This proves half-up for the rounding
#: sites the Basic Group I building chain passes through, in Commercial
#: Property. It is strong evidence for the rest of Property and for General
#: Liability -- same service, same rule language -- but GL's OI-70 is GL's to
#: close with a GL tie, and it is not closed here.
ROUNDING = "ROUND_HALF_UP"

#: What a null reaching arithmetic does in Property. **Decided 2026-09-17, on
#: evidence, after two other hypotheses were tested and failed.**
#:
#: ISO's service rates a New York risk this engine refused. Three explanations
#: were possible and all three were built and measured rather than argued:
#:
#:   refuse     contract §12.3 as written -- New York does not rate at all.
#:   zero       coerce null to 0 -- New York rates and returns $0 against ISO's
#:              $396. DISPROVEN, and instructively: it destroys ISO's own
#:              state-to-countrywide fallback idiom, because `Round(miss)`
#:              becomes a perfectly good 0 that `FirstNonNull` accepts, so the
#:              countrywide row is never read.
#:   propagate  a null stays null through arithmetic unless the node skips it.
#:              New York returns **$396 -- exactly ISO's figure** -- and the
#:              fallback idiom survives, because a null still lets
#:              `FirstNonNull` fall through.
#:
#: What `propagate` does today, each point confirmed against ISO live:
#: `Sum` and `Product` leave a null operand out (OI-110); `Subtract` leaves a
#: single null operand out and returns the other as it is (OI-115, 2026-09-30:
#: blank - 1,000 = 1,000 and 1,065 - blank = 1,065); `Divide` with a null
#: numerator is null (OI-110's $3 probe). A comparison with a null is NOT
#: simply false: "50,000 > blank" is true, in the engine and at ISO (chunk 20
#: C20-21, Fire Department). The paragraph above records the original choice.
#:
#: Measured blast radius of `propagate`: **nothing else moved.** Twelve General
#: Liability suites green under it, including the ones that compare against
#: ISO's own oracles; Property's three golden cases and six zero cases
#: unchanged; 43 of 47 jurisdictions still rate to their predicted figure.
#:
#: **The residual risk, stated rather than buried.** `refuse` fails loudly when
#: a live rating path hits a null; `propagate` returns null instead, and a null
#: can reach a premium quietly (`Sum` skips null operands by design). So this
#: trades a loud failure for a quiet one in paths nothing has exercised yet.
#: That trade is acceptable here because it is what ISO demonstrably does, and
#: because §12.3's real purpose -- never inventing a NUMBER -- is untouched:
#: propagation invents nothing, it reports "unknown". A null that reaches a
#: premium is worth its own guard, and that guard was then built: see
#: `Interpreter.guard_null_premium` and `PREMIUM_TARGETS`. Nulls flow freely
#: through intermediate arithmetic; writing one into `Premium` or
#: `ErcCalculatedTotalPremium` is refused. So the loudness moved from "any
#: arithmetic" to "the money", which is the boundary that matters.
#:
#: General Liability is deliberately NOT switched. It is unaffected either way
#: in every path measured, and its default stays `refuse` until someone wants
#: to make that change on GL's own evidence.
NULL_ARITHMETIC = "propagate"

#: Jurisdictions absent from the Property corpus outright -- not unfiled in the
#: current edition, absent from every edition. Recorded so their absence reads
#: as a known fact rather than as a resolver defect. Puerto Rico is present in
#: the corpus but out of scope for comparison work (no RAaS entitlement).
ABSENT_JURISDICTIONS = frozenset({"HI", "ID", "LA", "MS", "WA"})
